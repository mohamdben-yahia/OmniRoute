const INSPECT_HOST = "127.0.0.1";
const INSPECT_PORT = 60123;

async function getTarget() {
  const response = await fetch(`http://${INSPECT_HOST}:${INSPECT_PORT}/json/list`);
  const targets = await response.json();
  if (!Array.isArray(targets) || targets.length === 0) {
    throw new Error("No inspector targets returned");
  }
  return targets[0];
}

async function main() {
  const target = await getTarget();
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map();
  let nextId = 1;

  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", () => reject(new Error("WebSocket connection failed")), {
      once: true,
    });
  });

  socket.addEventListener("message", (event) => {
    const payload = JSON.parse(String(event.data));
    if (typeof payload.id === "number" && pending.has(payload.id)) {
      const { resolve, reject } = pending.get(payload.id);
      pending.delete(payload.id);
      if (payload.error) reject(new Error(payload.error.message || "Inspector error"));
      else resolve(payload.result);
    }
  });

  function send(method, params = {}) {
    const id = nextId++;
    socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
  }

  await send("Runtime.enable");

  const rootEval = await send("Runtime.evaluate", {
    expression: `(() => {
      const handles = process._getActiveHandles();
      const server = handles.find((handle) => {
        try {
          return handle && handle.constructor && handle.constructor.name === 'Server' && handle.address && typeof handle.address === 'function' && handle.address() && handle.address().port === 60166;
        } catch {
          return false;
        }
      });
      if (!server) return null;
      const listeners = typeof server.listeners === 'function' ? server.listeners('request') : [];
      return Array.isArray(listeners) ? listeners[0] : null;
    })()`,
    returnByValue: false,
    awaitPromise: true,
    replMode: true,
    generatePreview: true,
  });

  const fnObjectId = rootEval.result?.objectId;
  if (!fnObjectId) {
    throw new Error("Could not get request listener object id");
  }

  const fnProps = await send("Runtime.getProperties", {
    objectId: fnObjectId,
    ownProperties: true,
    accessorPropertiesOnly: false,
    generatePreview: true,
  });

  const scopeEntry = (fnProps.internalProperties || []).find((prop) => prop.name === "[[Scopes]]" && prop.value?.objectId);
  if (!scopeEntry?.value?.objectId) {
    throw new Error("Could not get [[Scopes]] object id");
  }

  const scopeArray = await send("Runtime.getProperties", {
    objectId: scopeEntry.value.objectId,
    ownProperties: true,
    accessorPropertiesOnly: false,
    generatePreview: true,
  });

  const output = {
    targetTitle: target.title,
    targetId: target.id,
    scopeSummaries: [],
    deepInspections: {},
  };

  for (const prop of scopeArray.result || []) {
    if (!/^\d+$/.test(prop.name)) continue;
    output.scopeSummaries.push({
      index: Number(prop.name),
      description: prop.value?.description || null,
      className: prop.value?.className || null,
      objectId: prop.value?.objectId || null,
      preview: prop.value?.preview || null,
    });
  }

  async function inspectObject(label, objectId, depth = 0) {
    const props = await send("Runtime.getProperties", {
      objectId,
      ownProperties: true,
      accessorPropertiesOnly: false,
      generatePreview: true,
    });
    const result = {
      properties: [],
      internalProperties: (props.internalProperties || []).map((prop) => ({
        name: prop.name,
        type: prop.value?.type || null,
        className: prop.value?.className || null,
        description: prop.value?.description || null,
        objectId: prop.value?.objectId || null,
      })),
    };

    for (const prop of props.result || []) {
      const entry = {
        name: prop.name,
        enumerable: !!prop.enumerable,
        type: prop.value?.type || null,
        className: prop.value?.className || null,
        description: prop.value?.description || null,
        value: prop.value?.value,
        objectId: prop.value?.objectId || null,
        preview: prop.value?.preview || null,
      };
      result.properties.push(entry);

      if (
        depth < 2 &&
        entry.objectId &&
        /csrf|token|server|client|routes|instance|proto|router|auth|language/i.test(entry.name)
      ) {
        try {
          result[`${entry.name}__nested`] = await inspectObject(`${label}.${entry.name}`, entry.objectId, depth + 1);
        } catch (error) {
          result[`${entry.name}__nestedError`] = error.message;
        }
      }
    }
    return result;
  }

  for (const summary of output.scopeSummaries) {
    if (!summary.objectId) continue;
    if (summary.index <= 2) {
      output.deepInspections[`scope_${summary.index}`] = await inspectObject(`scope_${summary.index}`, summary.objectId);
    }
  }

  socket.close();
  console.log(JSON.stringify(output, null, 2));
}

await main();
