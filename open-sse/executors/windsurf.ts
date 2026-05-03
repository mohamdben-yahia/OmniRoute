import { BaseExecutor, mergeUpstreamExtraHeaders, type ExecuteInput } from "./base.ts";
import { PROVIDERS } from "../config/constants.ts";
import { trimWindsurfModelPrefix } from "../config/windsurfModels.ts";
import { encodeField, wrapConnectRPCFrame } from "../utils/cursorProtobuf.ts";

const LEN = 2;
const ROLE = {
  USER: 1,
  ASSISTANT: 2,
} as const;
const FIELD = {
  REQUEST: 1,
  RAW_REQUEST_METADATA: 1,
  RAW_REQUEST_CHAT_MESSAGES: 2,
  RAW_REQUEST_SYSTEM_PROMPT_OVERRIDE: 3,
  RAW_REQUEST_CHAT_MODEL: 4,
  RAW_REQUEST_CHAT_MODEL_NAME: 5,
  FORMATTED_CHAT_MESSAGE_ROLE: 1,
  FORMATTED_CHAT_MESSAGE_HEADER: 2,
  FORMATTED_CHAT_MESSAGE_CONTENT: 3,
  FORMATTED_CHAT_MESSAGE_FOOTER: 4,
} as const;

function getWindsurfToken(credentials: ExecuteInput["credentials"]): string {
  const apiKey = typeof credentials.apiKey === "string" ? credentials.apiKey.trim() : "";
  if (apiKey) return apiKey;

  const accessToken =
    typeof credentials.accessToken === "string" ? credentials.accessToken.trim() : "";
  if (accessToken) return accessToken;

  return "";
}

function extractMessageText(content: unknown): string {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";

  return content
    .map((part) => {
      if (typeof part === "string") return part;
      if (part && typeof part === "object" && (part as { type?: unknown }).type === "text") {
        return typeof (part as { text?: unknown }).text === "string"
          ? ((part as { text: string }).text ?? "")
          : "";
      }
      return "";
    })
    .join("");
}

function encodeFormattedChatMessage(message: { role?: unknown; content?: unknown }): Uint8Array {
  const role = message.role === "assistant" ? ROLE.ASSISTANT : ROLE.USER;
  const content = extractMessageText(message.content);

  return encodeField(
    FIELD.RAW_REQUEST_CHAT_MESSAGES,
    LEN,
    new Uint8Array([
      ...encodeField(FIELD.FORMATTED_CHAT_MESSAGE_ROLE, 0, role),
      ...encodeField(FIELD.FORMATTED_CHAT_MESSAGE_CONTENT, LEN, content),
    ])
  );
}

function buildWindsurfConnectBody(body: Record<string, unknown>): Uint8Array {
  const messages = Array.isArray(body.messages) ? body.messages : [];
  const systemPrompt = typeof body.system === "string" ? body.system : "";
  const modelName = typeof body.model === "string" ? body.model : "";

  const rawRequest = new Uint8Array([
    ...messages.flatMap((message) => [...encodeFormattedChatMessage(message as Record<string, unknown>)]),
    ...encodeField(FIELD.RAW_REQUEST_SYSTEM_PROMPT_OVERRIDE, LEN, systemPrompt),
    ...encodeField(FIELD.RAW_REQUEST_CHAT_MODEL_NAME, LEN, modelName),
  ]);

  return wrapConnectRPCFrame(encodeField(FIELD.REQUEST, LEN, rawRequest), false);
}

export class WindsurfExecutor extends BaseExecutor {
  constructor() {
    super("windsurf", PROVIDERS.windsurf);
  }

  buildUrl() {
    return `${this.config.baseUrl}/exa.api_server_pb.ApiServerService/GetChatMessage`;
  }

  buildHeaders(credentials: ExecuteInput["credentials"], stream = true): Record<string, string> {
    const token = getWindsurfToken(credentials);
    const headers = super.buildHeaders(
      {
        ...credentials,
        apiKey: token || credentials.apiKey,
        accessToken: undefined,
      },
      stream
    );

    return {
      ...headers,
      "user-agent": "connect-go/1.17.0 (go1.23.4 X:nocoverageredesign)",
      "content-type": "application/connect+proto",
      "connect-protocol-version": "1",
      "accept-encoding": "identity",
      host: "server.codeium.com",
      "connect-accept-encoding": "gzip",
    };
  }

  transformRequest(
    model: string,
    body: unknown,
    stream: boolean,
    credentials: ExecuteInput["credentials"]
  ): unknown {
    void model;
    void stream;
    void credentials;

    const requestedModel =
      typeof (body as { model?: unknown })?.model === "string"
        ? ((body as { model: string }).model ?? "")
        : "";
    const resolvedModel = trimWindsurfModelPrefix(requestedModel) || requestedModel;

    if (!resolvedModel || typeof body !== "object" || body === null) {
      return body;
    }

    return {
      ...(body as Record<string, unknown>),
      model: resolvedModel,
    };
  }

  async execute(input: ExecuteInput) {
    const token = getWindsurfToken(input.credentials);
    if (!token) {
      return {
        response: new Response(
          JSON.stringify({
            error: {
              message: "Windsurf token is required. Add a Windsurf provider connection first.",
              type: "authentication_error",
              code: "token_required",
            },
          }),
          { status: 401, headers: { "Content-Type": "application/json" } }
        ),
        url: this.buildUrl(),
        headers: this.buildHeaders(input.credentials, input.stream),
        transformedBody: input.body,
      };
    }

    const credentials = {
      ...input.credentials,
      apiKey: token,
      accessToken: undefined,
    };
    const transformedBody = this.transformRequest(
      input.model,
      input.body,
      input.stream,
      credentials
    ) as Record<string, unknown>;
    const url = this.buildUrl();
    const headers = this.buildHeaders(credentials, input.stream);
    mergeUpstreamExtraHeaders(headers, input.upstreamExtraHeaders);
    const encodedBody = buildWindsurfConnectBody(transformedBody);

    const response = await fetch(url, {
      method: "POST",
      headers,
      body: encodedBody as unknown as BodyInit,
      signal: input.signal || undefined,
    });

    return {
      response,
      url,
      headers,
      transformedBody,
    };
  }
}

export default WindsurfExecutor;
