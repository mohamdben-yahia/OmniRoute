const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const Module = require('module');

const OUT = process.env.WINDSURF_HOOK_OUT || path.join('C:', 'Users', 'amine', 'OmniRoute', 'tmp_windsurf_capture', 'node-hook.jsonl');
fs.mkdirSync(path.dirname(OUT), { recursive: true });

const hints = ['model', 'models', 'registry', 'provider', 'chat/model', 'cascade', 'completion'];
function append(event) {
  fs.appendFileSync(OUT, JSON.stringify(event) + '\n', 'utf8');
}
function looksModelRelated(blob) {
  const s = String(blob || '').toLowerCase();
  return hints.some((h) => s.includes(h));
}
function wrapRequest(mod, proto) {
  const orig = mod.request;
  mod.request = function patchedRequest(...args) {
    const started = Date.now();
    const req = orig.apply(this, args);
    let bodyChunks = [];
    const origWrite = req.write;
    const origEnd = req.end;
    req.write = function(chunk, encoding, cb) {
      if (chunk) bodyChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk, encoding));
      return origWrite.call(this, chunk, encoding, cb);
    };
    req.end = function(chunk, encoding, cb) {
      if (chunk) bodyChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk, encoding));
      return origEnd.call(this, chunk, encoding, cb);
    };
    req.on('response', (res) => {
      const resChunks = [];
      res.on('data', (c) => resChunks.push(Buffer.from(c)));
      res.on('end', () => {
        const reqBody = Buffer.concat(bodyChunks).toString('utf8');
        const resBody = Buffer.concat(resChunks).toString('utf8');
        const host = req.getHeader('host') || (args[0] && args[0].host) || (args[0] && args[0].hostname) || '';
        const method = req.method || (args[0] && args[0].method) || 'GET';
        const pathName = req.path || (args[0] && args[0].path) || '';
        const url = `${proto}://${host}${pathName}`;
        append({
          ts: started / 1000,
          kind: 'node-http',
          url,
          method,
          headers: typeof req.getHeaders === 'function' ? req.getHeaders() : {},
          requestBody: reqBody,
          statusCode: res.statusCode,
          responseHeaders: res.headers,
          responseBody: resBody,
          model_related: looksModelRelated(url + '\n' + reqBody + '\n' + resBody),
        });
      });
    });
    return req;
  };
}
wrapRequest(http, 'http');
wrapRequest(https, 'https');

const origLoad = Module._load;
Module._load = function(request, parent, isMain) {
  const loaded = origLoad.apply(this, arguments);
  if (request === 'ws' || request === 'isomorphic-ws') {
    try {
      const WS = loaded;
      const origSend = WS.prototype.send;
      WS.prototype.send = function(data, ...rest) {
        append({ ts: Date.now() / 1000, kind: 'ws-send', url: this.url, payload: String(data), model_related: looksModelRelated(String(data)) });
        return origSend.call(this, data, ...rest);
      };
      const origOn = WS.prototype.on;
      WS.prototype.on = function(event, listener) {
        if (event === 'message') {
          return origOn.call(this, event, function(data, ...rest) {
            append({ ts: Date.now() / 1000, kind: 'ws-recv', url: this.url, payload: String(data), model_related: looksModelRelated(String(data)) });
            return listener.apply(this, [data, ...rest]);
          });
        }
        return origOn.call(this, event, listener);
      };
    } catch (_) {}
  }
  return loaded;
};

append({ ts: Date.now() / 1000, kind: 'init', message: 'node request hook active' });
