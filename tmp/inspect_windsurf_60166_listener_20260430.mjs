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
      const listeners = typeof server.listeners === 'function' ? server.listeners('request') : [];
      return {
        found: true,
        requestListenerCount: Array.isArray(listeners) ? listeners.length : null,
        serverObject: server,
        listeners,
      };
    })()`,
    returnByValue: false,
    awaitPromise: true,
    replMode: true,
    generatePreview: true,
  });

  const root = evalResult.result;
  const output = {
    targetTitle: target.title,
    targetId: target.id,
    root: {
      type: root.type,
      description: root.description,
      className: root.className || null,
      objectId: root.objectId || null,
      preview: root.preview || null,
      value: root.value,
    },
    properties: {},
    internals: {},
  };

  if (root.objectId) {
    const rootProps = await send("Runtime.getProperties", {
      objectId: root.objectId,
      ownProperties: true,
      accessorPropertiesOnly: false,
      generatePreview: true,
    });

    for (const prop of rootProps.result || []) {
      if (!prop || !prop.name) continue;
      output.properties[prop.name] = {
        enumerable: !!prop.enumerable,
        type: prop.value?.type || null,
        className: prop.value?.className || null,
        description: prop.value?.description || null,
        value: prop.value?.value,
        objectId: prop.value?.objectId || null,
        preview: prop.value?.preview || null,
      };
    }

    if (Array.isArray(rootProps.internalProperties)) {
      output.internals.root = rootProps.internalProperties.map((prop) => ({
        name: prop.name,
        type: prop.value?.type || null,
        className: prop.value?.className || null,
        description: prop.value?.description || null,
        objectId: prop.value?.objectId || null,
      }));
    }

    const listenerEntry = output.properties.listeners;
    if (listenerEntry?.objectId) {
      const listenerProps = await send("Runtime.getProperties", {
        objectId: listenerEntry.objectId,
        ownProperties: true,
        accessorPropertiesOnly: false,
        generatePreview: true,
      });
      output.listenerArray = {
        result: (listenerProps.result || []).map((prop) => ({
          name: prop.name,
          type: prop.value?.type || null,
          className: prop.value?.className || null,
          description: prop.value?.description || null,
          value: prop.value?.value,
          objectId: prop.value?.objectId || null,
          preview: prop.value?.preview || null,
        })),
        internalProperties: (listenerProps.internalProperties || []).map((prop) => ({
          name: prop.name,
          type: prop.value?.type || null,
          className: prop.value?.className || null,
          description: prop.value?.description || null,
          objectId: prop.value?.objectId || null,
        })),
      };

      const firstListener = (listenerProps.result || []).find((prop) => prop.name === "0" && prop.value?.objectId);
      if (firstListener?.value?.objectId) {
        const fnProps = await send("Runtime.getProperties", {
          objectId: firstListener.value.objectId,
          ownProperties: true,
          accessorPropertiesOnly: false,
          generatePreview: true,
        });
        output.firstListener = {
          meta: {
            type: firstListener.value.type,
            className: firstListener.value.className || null,
            description: firstListener.value.description || null,
            objectId: firstListener.value.objectId,
            preview: firstListener.value.preview || null,
          },
          properties: (fnProps.result || []).map((prop) => ({
            name: prop.name,
            type: prop.value?.type || null,
            className: prop.value?.className || null,
            description: prop.value?.description || null,
            value: prop.value?.value,
            objectId: prop.value?.objectId || null,
            preview: prop.value?.preview || null,
          })),
          internalProperties: (fnProps.internalProperties || []).map((prop) => ({
            name: prop.name,
            type: prop.value?.type || null,
            className: prop.value?.className || null,
            description: prop.value?.description || null,
            objectId: prop.value?.objectId || null,
          })),
        };

        const scopeEntry = (fnProps.internalProperties || []).find((prop) => prop.name === "[[Scopes]]" && prop.value?.objectId);
        if (scopeEntry?.value?.objectId) {
          const scopeProps = await send("Runtime.getProperties", {
            objectId: scopeEntry.value.objectId,
            ownProperties: true,
            accessorPropertiesOnly: false,
            generatePreview: true,
          });
          output.scopes = {
            entries: (scopeProps.result || []).map((prop) => ({
              name: prop.name,
              type: prop.value?.type || null,
              className: prop.value?.className || null,
              description: prop.value?.description || null,
              objectId: prop.value?.objectId || null,
              preview: prop.value?.preview || null,
            })),
          };
        }
      }
    }
  }

  socket.close();
  console.log(JSON.stringify(output, null, 2));
}

await main();
