const INSPECT_HOST = "127.0.0.1";
const INSPECT_PORT = 60123;

async function getTarget() {
  const response = await fetch(`http://${INSPECT_HOST}:${INSPECT_PORT}/json/list`);
  const targets = await response.json();
  if (!Array.isArray(targets) || targets.length === 0) throw new Error("No inspector targets returned");
  return targets[0];
}

async function main() {
  const target = await getTarget();
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map();
  let nextId = 1;

  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", () => reject(new Error("WebSocket connection failed")), { once: true });
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

  const evalResult = await send("Runtime.evaluate", {
    expression: `(() => {
      const handles = process._getActiveHandles();
      const server = handles.find((handle) => {
        try {
          return handle && handle.constructor && handle.constructor.name === 'Server' && handle.address && typeof handle.address === 'function' && handle.address() && handle.address().port === 60166;
        } catch {
          return false;
        }
      });
      if (!server) return { found: false };
      const listener = server.listeners('request')[0];
      return { found: true, listener };
    })()`,
    returnByValue: false,
    awaitPromise: true,
    replMode: true,
    generatePreview: true,
  });

  const rootObjectId = evalResult.result?.objectId;
  if (!rootObjectId) throw new Error("No root object id");

  const rootProps = await send("Runtime.getProperties", {
    objectId: rootObjectId,
    ownProperties: true,
    accessorPropertiesOnly: false,
    generatePreview: true,
  });

  const listenerObjId = (rootProps.result || []).find((p) => p.name === 'listener')?.value?.objectId;
  if (!listenerObjId) throw new Error("No listener object id");

  const listenerProps = await send("Runtime.getProperties", {
    objectId: listenerObjId,
    ownProperties: true,
    accessorPropertiesOnly: false,
    generatePreview: true,
  });

  const scopesObjId = (listenerProps.internalProperties || []).find((p) => p.name === '[[Scopes]]')?.value?.objectId;
  if (!scopesObjId) throw new Error("No scopes object id");

  const scopes = await send("Runtime.getProperties", {
    objectId: scopesObjId,
    ownProperties: true,
    accessorPropertiesOnly: false,
    generatePreview: true,
  });

  const blockScopeObjId = (scopes.result || []).find((p) => p.name === '1')?.value?.objectId;
  if (!blockScopeObjId) throw new Error("No block scope object id");

  const blockScope = await send("Runtime.getProperties", {
    objectId: blockScopeObjId,
    ownProperties: true,
    accessorPropertiesOnly: false,
    generatePreview: true,
  });

  const classObjId = (blockScope.result || []).find((p) => p.name === 'F')?.value?.objectId;
  if (!classObjId) throw new Error("No class F object id");

  const classProps = await send("Runtime.getProperties", {
    objectId: classObjId,
    ownProperties: true,
    accessorPropertiesOnly: false,
    generatePreview: true,
  });

  const instanceObjId = (classProps.result || []).find((p) => p.name === 'instance')?.value?.objectId;
  const output = {
    targetTitle: target.title,
    targetId: target.id,
    classProps: (classProps.result || []).map((p) => ({
      name: p.name,
      type: p.value?.type || null,
      className: p.value?.className || null,
      description: p.value?.description || null,
      value: p.value?.value,
      objectId: p.value?.objectId || null,
      preview: p.value?.preview || null,
    })),
  };

  if (instanceObjId) {
    const instanceProps = await send("Runtime.getProperties", {
      objectId: instanceObjId,
      ownProperties: true,
      accessorPropertiesOnly: false,
      generatePreview: true,
    });
    output.instanceProps = (instanceProps.result || []).map((p) => ({
      name: p.name,
      type: p.value?.type || null,
      className: p.value?.className || null,
      description: p.value?.description || null,
      value: p.value?.value,
      objectId: p.value?.objectId || null,
      preview: p.value?.preview || null,
    }));
  }

  socket.close();
  console.log(JSON.stringify(output, null, 2));
}

await main();
