// Shared query-string + share-URL helpers for xkcd-font docs.
//
// Public API on window.XkcdSite:
//   getParams()            → object of decoded query-string params (recomputed each call)
//   setParam(key, value)   → push key=value into ?query and update the share-URL input.
//                            value may be null/undefined to remove the key.
//   bindTextarea(el, key)  → mirror el's value to ?<key>=… on every input event; on load
//                            and popstate, restore el's value from that param if present.
//                            Fires a synthetic 'input' event after restoring so callers'
//                            own listeners can react.
//   onShareUrlReady(cb)    → cb() runs once the share-URL input is populated.

(function () {
    'use strict';

    function getParams() {
        var out = {};
        var q = window.location.search.replace(/^\?/, '');
        if (!q) return out;
        q.split('&').forEach(function (kv) {
            var eq = kv.indexOf('=');
            var k = decodeURIComponent((eq < 0 ? kv : kv.slice(0, eq)).replace(/\+/g, ' '));
            var v = eq < 0 ? '' : decodeURIComponent(kv.slice(eq + 1).replace(/\+/g, ' '));
            out[k] = v;
        });
        return out;
    }

    function buildQuery(params) {
        var parts = [];
        Object.keys(params).forEach(function (k) {
            var v = params[k];
            if (v === undefined || v === null) return;
            parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
        });
        return parts.length ? '?' + parts.join('&') : '';
    }

    function updateShareInput() {
        var input = document.getElementById('share-url-input');
        if (input) input.value = window.location.href;
    }

    function setParam(key, value) {
        var params = getParams();
        if (value === undefined || value === null) delete params[key];
        else params[key] = value;
        var url = window.location.pathname + buildQuery(params) + window.location.hash;
        history.replaceState({}, '', url);
        updateShareInput();
    }

    function bindTextarea(el, key) {
        function restore() {
            var params = getParams();
            if (Object.prototype.hasOwnProperty.call(params, key)) {
                el.value = params[key];
                el.dispatchEvent(new Event('input', {bubbles: true}));
            }
        }
        restore();
        window.addEventListener('popstate', restore);
        el.addEventListener('input', function () {
            setParam(key, el.value);
        });
    }

    function onShareUrlReady(cb) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function () {
                updateShareInput();
                cb && cb();
            });
        } else {
            updateShareInput();
            cb && cb();
        }
    }

    window.XkcdSite = {
        getParams: getParams,
        setParam: setParam,
        bindTextarea: bindTextarea,
        onShareUrlReady: onShareUrlReady,
    };
})();
