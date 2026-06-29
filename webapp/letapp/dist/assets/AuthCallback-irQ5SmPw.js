import {
  h as C,
  r as a,
  d as A,
  H as S,
  I as N,
  J as u,
  K as g,
  L as c,
  M as f,
  E as q,
  N as o,
  O as v,
  P as h,
  Q as d,
  l as k,
} from "./vendor-vue-D0UmDA62.js";
import { I as B } from "./vendor-icons-DUK5cEDW.js";
import { u as M } from "./index-CHWsF88q.js";
import { g as O, B as b } from "./vendor-naive-Co-etydz.js";
import "./vendor-monaco-CQJlpWvK.js";
const V = {
    class:
      "flex min-h-screen items-center justify-center bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50",
  },
  E = {
    class:
      "flex max-w-lg flex-col items-center gap-4 rounded-[2rem] border border-slate-200 bg-white px-6 py-6 text-center shadow-lg shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20",
  },
  I = { class: "text-sm font-bold" },
  L = {
    key: 0,
    class: "max-w-md text-xs leading-6 text-slate-500 dark:text-slate-400",
  },
  T = { key: 1, class: "flex flex-wrap justify-center gap-3" },
  H = C({
    __name: "AuthCallback",
    setup(j) {
      const s = S(),
        m = N(),
        p = O(),
        x = M(),
        y = a("正在完成登录，请稍候..."),
        n = a(""),
        l = a("/"),
        r = a(!1),
        _ = (t) => {
          const e = Array.isArray(t) ? String(t[0] ?? "/") : String(t || "/");
          return e.startsWith("/") ? e : "/";
        },
        w = () => {
          x.startOAuthLogin("iOSClub", l.value, !0);
        };
      return (
        A(async () => {
          l.value = _(s.query.next);
          try {
            (x.completeOAuthCallback(s.query),
              p.success("登录成功"),
              await m.replace(l.value));
          } catch (t) {
            const e = t instanceof Error ? t.message : "登录失败，请稍后重试。",
              i = Array.isArray(s.query.provider)
                ? String(s.query.provider[0] ?? "")
                : String(s.query.provider ?? "");
            ((y.value = e),
              (n.value = i
                ? `登录提供方：${i}。如果持续失败，说明问题很可能出在第三方统一认证页面或其会话服务。`
                : "如果持续失败，说明问题很可能出在第三方统一认证页面或其会话服务。"),
              (r.value = !0),
              p.error(e));
          }
        }),
        (t, e) => (
          d(),
          u("div", V, [
            g("div", E, [
              c(
                o(B),
                {
                  icon: r.value
                    ? "material-symbols:error-outline-rounded"
                    : "material-symbols:progress-activity",
                  class: q([
                    "h-8 w-8",
                    r.value ? "text-rose-500" : "animate-spin text-cyan-500",
                  ]),
                },
                null,
                8,
                ["icon", "class"],
              ),
              g("span", I, v(y.value), 1),
              n.value ? (d(), u("p", L, v(n.value), 1)) : f("", !0),
              r.value
                ? (d(),
                  u("div", T, [
                    c(
                      o(b),
                      { type: "primary", onClick: w },
                      {
                        default: h(() => [
                          ...(e[1] || (e[1] = [k("重新登录", -1)])),
                        ]),
                        _: 1,
                      },
                    ),
                    c(
                      o(b),
                      {
                        tertiary: "",
                        onClick: e[0] || (e[0] = (i) => o(m).push("/")),
                      },
                      {
                        default: h(() => [
                          ...(e[2] || (e[2] = [k("返回首页", -1)])),
                        ]),
                        _: 1,
                      },
                    ),
                  ]))
                : f("", !0),
            ]),
          ])
        )
      );
    },
  });
export { H as default };
