const __vite__mapDeps = (
  i,
  m = __vite__mapDeps,
  d = m.f ||
    (m.f = [
      "assets/Home-CoeVi5xn.js",
      "assets/vendor-icons-DUK5cEDW.js",
      "assets/vendor-vue-D0UmDA62.js",
      "assets/vendor-naive-Co-etydz.js",
      "assets/vendor-monaco-CQJlpWvK.js",
      "assets/vendor-monaco-Ck3IbhyB.css",
      "assets/Home-sp2UZ7Z6.css",
      "assets/Playground-BfTZjueS.js",
      "assets/Playground-DL-MPlTQ.css",
      "assets/Learn-Dk4tAsZi.js",
      "assets/MarkdownComponent-J92OtoSn.js",
      "assets/vendor-markdown-HlADSkmp.js",
      "assets/vendor-prism-DA50wpei.js",
      "assets/MarkdownComponent-UUfociu3.css",
      "assets/Learn-CoCjPmOR.css",
      "assets/Announcements-C8x2hTQo.js",
      "assets/Announcements-CvrKmVlL.css",
      "assets/Login-CWKUFn9f.js",
      "assets/Login-BODVWaZj.css",
      "assets/AuthCallback-Bm3huQjk.js",
      "assets/Dashboard-Bc5JRRr4.js",
      "assets/Dashboard-BXQvMu0t.css",
      "assets/Users-QdQaWben.js",
      "assets/Users-B3-PxQbJ.css",
    ]),
) => i.map((i) => d[i]);
var Se = Object.defineProperty;
var xe = (e, s, o) =>
  s in e
    ? Se(e, s, { enumerable: !0, configurable: !0, writable: !0, value: o })
    : (e[s] = o);
var Q = (e, s, o) => xe(e, typeof s != "symbol" ? s + "" : s, o);
import {
  _ as de,
  r as b,
  c as C,
  h as se,
  $ as me,
  d as he,
  S as G,
  N as d,
  P as S,
  a0 as j,
  Q as v,
  L as h,
  z as Ee,
  J as w,
  I as pe,
  K as n,
  E as R,
  M,
  F as X,
  V as q,
  O as H,
  Z as ie,
  R as Le,
  q as Ae,
  H as Ce,
  a1 as Ie,
  a2 as Oe,
  a3 as Te,
  a4 as Pe,
} from "./vendor-vue-D0UmDA62.js";
import {
  l as Re,
  n as Ne,
  o as $e,
  p as De,
  q as le,
  s as Me,
  t as Ve,
} from "./vendor-naive-Co-etydz.js";
import { _ as I } from "./vendor-monaco-CQJlpWvK.js";
import { I as A } from "./vendor-icons-DUK5cEDW.js";
(function () {
  const s = document.createElement("link").relList;
  if (s && s.supports && s.supports("modulepreload")) return;
  for (const t of document.querySelectorAll('link[rel="modulepreload"]')) i(t);
  new MutationObserver((t) => {
    for (const l of t)
      if (l.type === "childList")
        for (const p of l.addedNodes)
          p.tagName === "LINK" && p.rel === "modulepreload" && i(p);
  }).observe(document, { childList: !0, subtree: !0 });
  function o(t) {
    const l = {};
    return (
      t.integrity && (l.integrity = t.integrity),
      t.referrerPolicy && (l.referrerPolicy = t.referrerPolicy),
      t.crossOrigin === "use-credentials"
        ? (l.credentials = "include")
        : t.crossOrigin === "anonymous"
          ? (l.credentials = "omit")
          : (l.credentials = "same-origin"),
      l
    );
  }
  function i(t) {
    if (t.ep) return;
    t.ep = !0;
    const l = o(t);
    fetch(t.href, l);
  }
})();
const _e = de("theme", () => {
    const e = "appThemePreference",
      s = b(localStorage.getItem(e) || "system"),
      o = b(window.matchMedia("(prefers-color-scheme: dark)").matches),
      i = (m) => {
        document.documentElement.classList.toggle("dark", m);
      },
      t = C({
        get() {
          return s.value === "dark" ? !0 : s.value === "light" ? !1 : o.value;
        },
        set(m) {
          ((s.value = m ? "dark" : "light"),
            localStorage.setItem(e, s.value),
            i(m));
        },
      }),
      l = C(() => (t.value ? Re : null));
    return {
      isDark: t,
      theme: l,
      userPreference: s,
      setThemePreference: (m) => {
        ((s.value = m), localStorage.setItem(e, m), i(t.value));
      },
      toggleTheme: () => {
        t.value = !t.value;
      },
      init: () => {
        (window
          .matchMedia("(prefers-color-scheme: dark)")
          .addEventListener("change", (y) => {
            ((o.value = y.matches), s.value === "system" && i(t.value));
          }),
          i(t.value));
      },
    };
  }),
  fe = "https://ojapi.xauat.site",
  oe = "auth_storage_mode";
class ge extends Error {
  constructor(o, i, t) {
    super(o);
    Q(this, "status");
    Q(this, "payload");
    ((this.name = "ApiError"), (this.status = i), (this.payload = t));
  }
}
const Z = () => (localStorage.getItem(oe) === "session" ? "session" : "local"),
  He = (e) => {
    localStorage.setItem(oe, e);
  },
  Ue = () => {
    localStorage.removeItem(oe);
  },
  P = (e = Z()) => (e === "session" ? sessionStorage : localStorage),
  Ke = () => P().getItem("access_token"),
  je = async (e) => {
    if ((e.headers.get("content-type") || "").includes("application/json"))
      return e.json();
    const o = await e.text();
    return o ? { message: o } : {};
  };
async function $(e, s = {}) {
  const { skipAuth: o, headers: i, body: t, ...l } = s,
    p = new Headers(i);
  if (
    (t &&
      !(t instanceof FormData) &&
      !p.has("Content-Type") &&
      p.set("Content-Type", "application/json"),
    !o)
  ) {
    const m = Ke();
    m && !p.has("Authorization") && p.set("Authorization", `Bearer ${m}`);
  }
  const u = await fetch(`${fe}${e}`, { ...l, body: t, headers: p }),
    f = await je(u);
  if (!u.ok) {
    const m =
      typeof f == "object" && f && "error" in f
        ? String(f.error)
        : `请求失败，状态码 ${u.status}`;
    throw new ge(m, u.status, f);
  }
  return f;
}
const ee = "access_token",
  te = "refresh_token",
  V = "user_info",
  D = "oauth_login_remember",
  ve = "oauth_login_provider",
  be = "oauth_login_next",
  O = (e) =>
    Array.isArray(e) ? String(e[0] ?? "") : e == null ? "" : String(e),
  ze = (e, s = P()) => {
    const o = s.getItem(e);
    if (!o) return null;
    try {
      return JSON.parse(o);
    } catch {
      return (s.removeItem(e), null);
    }
  },
  ce = () => {
    for (const e of [localStorage, sessionStorage])
      (e.removeItem(ee), e.removeItem(te), e.removeItem(V));
    (sessionStorage.removeItem(D),
      sessionStorage.removeItem(ve),
      sessionStorage.removeItem(be),
      Ue());
  },
  Je = (e, s) => {
    const o = `${e} ${s}`.trim().toLowerCase();
    return o.includes("timeout") || o.includes("超时")
      ? "登录请求超时，请稍后重试。"
      : o.includes("会话创建失败")
        ? "第三方登录页面未能创建授权会话，请稍后重试或联系统一认证服务维护方。"
        : o.includes("access_denied") ||
            o.includes("denied") ||
            o.includes("拒绝")
          ? "你已取消授权，登录未完成。"
          : o.includes("missing") || o.includes("token") || o.includes("缺少")
            ? "登录回调缺少必要凭证，请重新发起登录。"
            : s || e || "登录失败，请稍后重试。";
  },
  z = de("auth", () => {
    const e = b(Z()),
      s = b(P(e.value).getItem(ee) || ""),
      o = b(P(e.value).getItem(te) || ""),
      i = b(ze(V, P(e.value))),
      t = b([]),
      l = b(!1),
      p = b(!1),
      u = C(() => !!s.value),
      f = C(
        () =>
          i.value?.name || i.value?.username || i.value?.email || "已登录用户",
      ),
      m = C(() => i.value?.role || "member"),
      y = (a) => a instanceof ge && [400, 401, 403].includes(a.status),
      k = (a, r = {}) => {
        const g =
          r.storageMode ??
          (r.remember === void 0 ? Z() : r.remember ? "local" : "session");
        (ce(), He(g), (e.value = g));
        const _ = P(g);
        ((s.value = a.access_token),
          (o.value = a.refresh_token),
          (i.value = a.user_info ?? null),
          _.setItem(ee, a.access_token),
          _.setItem(te, a.refresh_token),
          a.user_info
            ? _.setItem(V, JSON.stringify(a.user_info))
            : _.removeItem(V));
      },
      x = () => {
        ((s.value = ""),
          (o.value = ""),
          (i.value = null),
          (e.value = "local"),
          ce());
      },
      E = (a, r = "/", g = !0) => {
        sessionStorage.setItem(D, g ? "1" : "0");
        const _ = r.startsWith("/") ? r : "/";
        (sessionStorage.setItem(ve, a), sessionStorage.setItem(be, _));
        const c = new URL(`${fe}/auth/login/${encodeURIComponent(a)}`);
        (c.searchParams.set("next", _), (window.location.href = c.toString()));
      },
      N = (a = "/", r = !0) => {
        E("github", a, r);
      },
      J = (a) => {
        const r = O(a.error);
        if (r) {
          const we = O(a.error_description);
          throw (sessionStorage.removeItem(D), new Error(Je(r, we)));
        }
        const g = O(a.access_token),
          _ = O(a.refresh_token);
        if (!g || !_)
          throw (
            sessionStorage.removeItem(D),
            new Error("登录回调缺少必要令牌，请重新发起登录。")
          );
        let c;
        const T = O(a.user_info);
        if (T)
          try {
            c = JSON.parse(T);
          } catch {
            try {
              c = JSON.parse(decodeURIComponent(T));
            } catch {
              c = void 0;
            }
          }
        const ne = O(sessionStorage.getItem(D));
        sessionStorage.removeItem(D);
        const re = ne === "1" ? !0 : ne === "0" ? !1 : void 0;
        k(
          {
            access_token: g,
            refresh_token: _,
            expires_in: Number(O(a.expires_in) || 0),
            token_type: O(a.token_type) || "Bearer",
            user_info: c,
          },
          re === void 0 ? {} : { remember: re },
        );
      },
      L = async (a, r, g = !0) => {
        const _ = await $("/auth/login/password", {
            method: "POST",
            skipAuth: !0,
            body: JSON.stringify({ identifier: a, password: r }),
          }),
          c = { ..._.tokens, user_info: _.tokens.user_info ?? _.user_info };
        return (k(c, { remember: g }), c);
      },
      F = async (a, r, g, _ = !0) => {
        const c = await $(`/auth/login/${encodeURIComponent(a)}/password`, {
            method: "POST",
            skipAuth: !0,
            body: JSON.stringify({ identifier: r, password: g, remember: _ }),
          }),
          T = { ...c.tokens, user_info: c.tokens.user_info ?? c.user_info };
        return (k(T, { remember: _ }), T);
      },
      B = async () => {
        p.value = !0;
        try {
          const a = await $("/auth/providers", { skipAuth: !0 });
          return (
            (t.value = Array.isArray(a.providers) ? a.providers : []),
            t.value
          );
        } catch {
          return ((t.value = []), []);
        } finally {
          p.value = !1;
        }
      },
      U = async (a = {}) => {
        if (!s.value) return !1;
        l.value = !0;
        try {
          const r = await $("/auth/verify");
          return (
            r.user_info &&
              ((i.value = r.user_info),
              P(e.value).setItem(V, JSON.stringify(r.user_info))),
            r.valid
          );
        } catch (r) {
          return (a.clearOnFailure !== !1 && y(r) && x(), !1);
        } finally {
          l.value = !1;
        }
      },
      K = async () => {
        if (!o.value) return (x(), !1);
        try {
          const a = await $("/auth/refresh", {
            method: "POST",
            skipAuth: !0,
            body: JSON.stringify({ refresh_token: o.value }),
          });
          return (k(a, { storageMode: e.value }), !0);
        } catch (a) {
          return (y(a) && x(), !1);
        }
      };
    return {
      accessToken: s,
      refreshToken: o,
      userInfo: i,
      userRole: m,
      supportedProviders: t,
      isAuthenticated: u,
      isVerifying: l,
      isLoadingProviders: p,
      displayName: f,
      setSession: k,
      clearSession: x,
      startOAuthLogin: E,
      startGithubLogin: N,
      completeOAuthCallback: J,
      loginWithPassword: L,
      loginWithProviderPassword: F,
      loadSupportedProviders: B,
      verify: U,
      refresh: K,
      restoreSession: async () =>
        !s.value && !o.value
          ? !1
          : (s.value ? await U({ clearOnFailure: !1 }) : !1)
            ? !0
            : o.value
              ? K()
              : (x(), !1),
      logout: async () => {
        if (s.value)
          try {
            await $("/auth/logout", { method: "POST" });
          } catch {}
        x();
      },
    };
  }),
  Fe = se({
    __name: "App",
    setup(e) {
      const s = _e(),
        o = z(),
        { theme: i } = me(s),
        { init: t } = s;
      return (
        he(() => {
          (t(), o.restoreSession());
        }),
        (l, p) => {
          const u = j("router-view");
          return (
            v(),
            G(
              d(Ne),
              { theme: d(i) },
              {
                default: S(() => [
                  h(d($e), null, {
                    default: S(() => [
                      h(d(De), null, { default: S(() => [h(u)]), _: 1 }),
                    ]),
                    _: 1,
                  }),
                ]),
                _: 1,
              },
              8,
              ["theme"],
            )
          );
        }
      );
    },
  }),
  ue = "/assets/logo.png",
  Be = {
    class:
      "min-h-screen bg-slate-50 text-slate-950 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-50",
  },
  We = { class: "flex h-20 items-center justify-between gap-3 px-5" },
  Ye = { key: 0, class: "min-w-0" },
  Qe = { class: "flex-1 space-y-2 px-4 pb-6" },
  Ge = { key: 0, class: "truncate" },
  Xe = { class: "border-t border-slate-200 p-4 dark:border-slate-800" },
  qe = ["aria-label"],
  Ze = { key: 0, class: "text-sm font-bold" },
  et = {
    class: "flex min-h-14 w-full min-w-0 items-center justify-between gap-3",
  },
  tt = {
    class: "ml-auto flex min-w-0 items-center justify-end gap-2 sm:gap-3",
  },
  st = { class: "relative shrink-0" },
  ot = {
    key: 0,
    class:
      "absolute right-0 top-[calc(100%+0.75rem)] z-50 w-[min(18rem,calc(100vw-1.5rem))] rounded-[1.75rem] border border-slate-200 bg-white p-3 shadow-2xl shadow-slate-200/70 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/40",
  },
  at = ["onClick"],
  nt = ["aria-label"],
  rt = { class: "truncate" },
  it = { class: "pt-20" },
  lt = 288,
  ct = 96,
  ut = se({
    __name: "MainLayout",
    setup(e) {
      const s = [
          { label: "首页", to: "/", icon: "material-symbols:home-rounded" },
          {
            label: "在线编辑器",
            to: "/playground",
            icon: "material-symbols:code-rounded",
          },
          {
            label: "学习资源",
            to: "/learn",
            icon: "material-symbols:school-rounded",
          },
          {
            label: "公告",
            to: "/announcements",
            icon: "material-symbols:campaign-rounded",
          },
        ],
        o = pe(),
        i = _e(),
        t = z(),
        { isDark: l } = me(i),
        { toggleTheme: p } = i,
        u = b(!0),
        f = b(!1),
        m = b(!1),
        y = b(!1),
        k = C(() => (u.value ? lt : ct)),
        x = C(() =>
          y.value
            ? { paddingLeft: `${k.value + 16}px`, paddingRight: "16px" }
            : void 0,
        ),
        E = C(() => ({
          ...(y.value ? { paddingLeft: `${k.value}px` } : {}),
          "--app-content-left": y.value ? `${k.value}px` : "0px",
        })),
        N = () => {
          y.value = window.innerWidth >= 768;
        },
        J = () => {
          u.value = !u.value;
        },
        L = () => {
          f.value = !1;
        },
        F = () => {
          (p(), L());
        },
        B = () => {
          (L(),
            t.startOAuthLogin("iOSClub", o.currentRoute.value.fullPath, !0));
        },
        U = async () => {
          (L(), await t.logout());
        },
        K = async (a) => {
          (L(), await o.push(a));
        },
        W = () => {
          m.value = window.scrollY > 10;
        },
        Y = (a) => {
          const r = a.target;
          !r?.closest(".icon-button") && !r?.closest(".menu-link") && L();
        };
      return (
        he(() => {
          (N(),
            window.addEventListener("scroll", W),
            window.addEventListener("click", Y),
            window.addEventListener("resize", N));
        }),
        Ee(() => {
          (window.removeEventListener("scroll", W),
            window.removeEventListener("click", Y),
            window.removeEventListener("resize", N));
        }),
        (a, r) => {
          const g = j("router-link"),
            _ = j("router-view");
          return (
            v(),
            w("div", Be, [
              h(
                d(le),
                { "has-sider": "", class: "min-h-screen bg-transparent" },
                {
                  default: S(() => [
                    n(
                      "aside",
                      {
                        class: R([
                          "fixed left-0 top-0 z-50 hidden h-screen flex-col border-r border-white/70 bg-white/88 shadow-2xl shadow-slate-200/60 backdrop-blur-2xl transition-all duration-300 dark:border-slate-800/80 dark:bg-slate-950/88 dark:shadow-black/30 md:flex",
                          u.value ? "w-72" : "w-24",
                        ]),
                      },
                      [
                        n("div", We, [
                          h(
                            g,
                            {
                              to: "/",
                              class:
                                "group flex min-w-0 items-center gap-3 overflow-hidden",
                              onClick: L,
                            },
                            {
                              default: S(() => [
                                r[2] ||
                                  (r[2] = n(
                                    "span",
                                    {
                                      class:
                                        "relative grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-white shadow-lg shadow-cyan-500/15 dark:bg-slate-950",
                                    },
                                    [
                                      n("img", {
                                        src: ue,
                                        alt: "Let Coding Logo",
                                        class:
                                          "h-8 w-8 transition-transform group-hover:scale-110",
                                      }),
                                    ],
                                    -1,
                                  )),
                                u.value
                                  ? (v(),
                                    w("div", Ye, [
                                      ...(r[1] ||
                                        (r[1] = [
                                          n(
                                            "div",
                                            {
                                              class:
                                                "truncate text-lg font-black tracking-tight",
                                            },
                                            "Let Coding",
                                            -1,
                                          ),
                                          n(
                                            "div",
                                            {
                                              class:
                                                "-mt-1 text-[11px] font-medium uppercase tracking-[0.24em] text-slate-400",
                                            },
                                            "Online Judge",
                                            -1,
                                          ),
                                        ])),
                                    ]))
                                  : M("", !0),
                              ]),
                              _: 1,
                            },
                          ),
                        ]),
                        n("nav", Qe, [
                          (v(),
                          w(
                            X,
                            null,
                            q(s, (c) =>
                              h(
                                g,
                                {
                                  key: c.to,
                                  to: c.to,
                                  class: R([
                                    "sidebar-link",
                                    u.value
                                      ? "justify-start px-4"
                                      : "justify-center px-0",
                                  ]),
                                  onClick: L,
                                },
                                {
                                  default: S(() => [
                                    h(
                                      d(A),
                                      {
                                        icon: c.icon,
                                        class: "h-5 w-5 shrink-0",
                                      },
                                      null,
                                      8,
                                      ["icon"],
                                    ),
                                    u.value
                                      ? (v(), w("span", Ge, H(c.label), 1))
                                      : M("", !0),
                                  ]),
                                  _: 2,
                                },
                                1032,
                                ["to", "class"],
                              ),
                            ),
                            64,
                          )),
                        ]),
                        n("div", Xe, [
                          n(
                            "button",
                            {
                              class: R([
                                "sidebar-toggle w-full",
                                u.value
                                  ? "justify-between px-4"
                                  : "justify-center",
                              ]),
                              "aria-label": u.value
                                ? "收起侧边栏"
                                : "展开侧边栏",
                              onClick: J,
                            },
                            [
                              u.value
                                ? (v(), w("span", Ze, "收起"))
                                : M("", !0),
                              h(
                                d(A),
                                {
                                  icon: u.value
                                    ? "material-symbols:chevron-left"
                                    : "material-symbols:chevron-right",
                                  class: "h-5 w-5",
                                },
                                null,
                                8,
                                ["icon"],
                              ),
                            ],
                            10,
                            qe,
                          ),
                        ]),
                      ],
                      2,
                    ),
                    h(d(le), null, {
                      default: S(() => [
                        h(
                          d(Me),
                          {
                            class: R([
                              "fixed left-0 right-0 top-0 z-40 border-b border-white/60 bg-white/86 shadow-sm shadow-slate-200/40 backdrop-blur-2xl transition-all duration-300 dark:border-slate-800/80 dark:bg-slate-950/86 dark:shadow-black/20",
                              { "header-compact": m.value },
                            ]),
                          },
                          {
                            default: S(() => [
                              n(
                                "div",
                                {
                                  class:
                                    "h-auto min-h-20 w-full px-3 py-3 sm:px-4 lg:px-6",
                                  style: ie(x.value),
                                },
                                [
                                  n("div", et, [
                                    h(
                                      g,
                                      {
                                        to: "/",
                                        class:
                                          "flex min-w-0 items-center gap-3 md:hidden",
                                        onClick: L,
                                      },
                                      {
                                        default: S(() => [
                                          ...(r[3] ||
                                            (r[3] = [
                                              n(
                                                "span",
                                                {
                                                  class:
                                                    "grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-white dark:bg-slate-950",
                                                },
                                                [
                                                  n("img", {
                                                    src: ue,
                                                    alt: "Let Coding Logo",
                                                    class: "h-7 w-7",
                                                  }),
                                                ],
                                                -1,
                                              ),
                                              n(
                                                "span",
                                                {
                                                  class:
                                                    "truncate text-base font-black",
                                                },
                                                "Let Coding",
                                                -1,
                                              ),
                                            ])),
                                        ]),
                                        _: 1,
                                      },
                                    ),
                                    n("div", tt, [
                                      n("div", st, [
                                        n(
                                          "button",
                                          {
                                            class: "icon-button",
                                            "aria-label": "打开导航菜单",
                                            onClick:
                                              r[0] ||
                                              (r[0] = Le(
                                                (c) => (f.value = !f.value),
                                                ["stop"],
                                              )),
                                          },
                                          [
                                            h(
                                              d(A),
                                              {
                                                icon: f.value
                                                  ? "material-symbols:close-rounded"
                                                  : "material-symbols:menu-rounded",
                                                class: "h-6 w-6",
                                              },
                                              null,
                                              8,
                                              ["icon"],
                                            ),
                                          ],
                                        ),
                                        h(
                                          Ae,
                                          { name: "fade-scale" },
                                          {
                                            default: S(() => [
                                              f.value
                                                ? (v(),
                                                  w("div", ot, [
                                                    (v(),
                                                    w(
                                                      X,
                                                      null,
                                                      q(s, (c) =>
                                                        n(
                                                          "button",
                                                          {
                                                            key: `${c.to}-menu`,
                                                            type: "button",
                                                            class: "menu-link",
                                                            onClick: (T) =>
                                                              K(c.to),
                                                          },
                                                          [
                                                            h(
                                                              d(A),
                                                              {
                                                                icon: c.icon,
                                                                class:
                                                                  "h-5 w-5",
                                                              },
                                                              null,
                                                              8,
                                                              ["icon"],
                                                            ),
                                                            n(
                                                              "span",
                                                              null,
                                                              H(c.label),
                                                              1,
                                                            ),
                                                          ],
                                                          8,
                                                          at,
                                                        ),
                                                      ),
                                                      64,
                                                    )),
                                                  ]))
                                                : M("", !0),
                                            ]),
                                            _: 1,
                                          },
                                        ),
                                      ]),
                                      n(
                                        "button",
                                        {
                                          class: "icon-button shrink-0",
                                          "aria-label": d(l)
                                            ? "切换到浅色模式"
                                            : "切换到深色模式",
                                          onClick: F,
                                        },
                                        [
                                          d(l)
                                            ? (v(),
                                              G(d(A), {
                                                key: 1,
                                                icon: "material-symbols:dark-mode",
                                                class: "h-5 w-5 text-cyan-300",
                                              }))
                                            : (v(),
                                              G(d(A), {
                                                key: 0,
                                                icon: "material-symbols:light-mode",
                                                class: "h-5 w-5 text-amber-500",
                                              })),
                                        ],
                                        8,
                                        nt,
                                      ),
                                      d(t).isAuthenticated
                                        ? (v(),
                                          w(
                                            "button",
                                            {
                                              key: 1,
                                              class: "secondary-pill shrink-0",
                                              onClick: U,
                                            },
                                            [
                                              n(
                                                "span",
                                                rt,
                                                "退出 " + H(d(t).displayName),
                                                1,
                                              ),
                                            ],
                                          ))
                                        : (v(),
                                          w(
                                            "button",
                                            {
                                              key: 0,
                                              class: "primary-pill shrink-0",
                                              onClick: B,
                                            },
                                            " 登录 ",
                                          )),
                                    ]),
                                  ]),
                                ],
                                4,
                              ),
                            ]),
                            _: 1,
                          },
                          8,
                          ["class"],
                        ),
                        h(
                          d(Ve),
                          {
                            class: "transition-all duration-300",
                            style: ie(E.value),
                          },
                          { default: S(() => [n("div", it, [h(_)])]), _: 1 },
                          8,
                          ["style"],
                        ),
                      ]),
                      _: 1,
                    }),
                  ]),
                  _: 1,
                },
              ),
            ])
          );
        }
      );
    },
  }),
  ye = (e, s) => {
    const o = e.__vccOpts || e;
    for (const [i, t] of s) o[i] = t;
    return o;
  },
  dt = ye(ut, [["__scopeId", "data-v-fe417e00"]]),
  mt = {
    class:
      "min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50",
  },
  ht = {
    class:
      "sticky top-0 z-50 border-b border-slate-200 bg-white/85 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/85",
  },
  pt = { class: "flex h-16 items-center justify-between px-4" },
  _t = { class: "flex items-center gap-3" },
  ft = ["aria-label"],
  gt = { class: "flex items-center gap-3" },
  vt = {
    class:
      "hidden text-sm font-bold text-slate-500 dark:text-slate-400 md:inline",
  },
  bt = { class: "flex" },
  yt = { class: "p-4" },
  kt = ["onClick"],
  wt = { key: 0 },
  St = se({
    __name: "AdminLayout",
    setup(e) {
      const s = pe(),
        o = Ce(),
        i = z(),
        t = b(!0),
        l = [
          {
            title: "仪表盘",
            icon: "material-symbols:dashboard",
            route: "/admin/dashboard",
          },
          {
            title: "用户管理",
            icon: "material-symbols:people",
            route: "/admin/users",
          },
          { title: "返回首页", icon: "material-symbols:home", route: "/" },
        ],
        p = C(() => o.path),
        u = () => {
          t.value = !t.value;
        },
        f = (y) => {
          s.push(y);
        },
        m = async () => {
          (await i.logout(), s.push("/"));
        };
      return (y, k) => {
        const x = j("router-view");
        return (
          v(),
          w("div", mt, [
            n("header", ht, [
              n("div", pt, [
                n("div", _t, [
                  n(
                    "button",
                    {
                      class: "admin-icon-button",
                      "aria-label": t.value ? "收起侧边栏" : "展开侧边栏",
                      onClick: u,
                    },
                    [
                      h(
                        d(A),
                        {
                          icon: t.value
                            ? "material-symbols:chevron-left"
                            : "material-symbols:chevron-right",
                          class: "h-6 w-6",
                        },
                        null,
                        8,
                        ["icon"],
                      ),
                    ],
                    8,
                    ft,
                  ),
                  k[0] ||
                    (k[0] = n(
                      "h1",
                      { class: "text-xl font-black" },
                      "Let Coding 管理后台",
                      -1,
                    )),
                ]),
                n("div", gt, [
                  n("span", vt, H(d(i).displayName), 1),
                  n(
                    "button",
                    {
                      class: "admin-icon-button",
                      "aria-label": "退出登录",
                      onClick: m,
                    },
                    [
                      h(d(A), {
                        icon: "material-symbols:logout",
                        class: "h-6 w-6 text-rose-500",
                      }),
                    ],
                  ),
                ]),
              ]),
            ]),
            n("div", bt, [
              n(
                "aside",
                {
                  class: R([
                    "fixed bottom-0 top-16 z-40 overflow-y-auto border-r border-slate-200 bg-white shadow-lg shadow-slate-200/50 transition-all duration-300 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20",
                    t.value ? "w-64" : "w-20",
                  ]),
                },
                [
                  n("nav", yt, [
                    (v(),
                    w(
                      X,
                      null,
                      q(l, (E) =>
                        n(
                          "button",
                          {
                            key: E.route,
                            class: R([
                              "mb-2 flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left font-bold transition",
                              p.value === E.route
                                ? "bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200"
                                : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
                            ]),
                            onClick: (N) => f(E.route),
                          },
                          [
                            h(
                              d(A),
                              { icon: E.icon, class: "h-6 w-6 shrink-0" },
                              null,
                              8,
                              ["icon"],
                            ),
                            t.value
                              ? (v(), w("span", wt, H(E.title), 1))
                              : M("", !0),
                          ],
                          10,
                          kt,
                        ),
                      ),
                      64,
                    )),
                  ]),
                ],
                2,
              ),
              n(
                "main",
                {
                  class: R([
                    "flex-1 p-6 transition-all duration-300",
                    t.value ? "ml-64" : "ml-20",
                  ]),
                },
                [h(x)],
                2,
              ),
            ]),
          ])
        );
      };
    },
  }),
  xt = ye(St, [["__scopeId", "data-v-864ff73a"]]),
  Et = [
    {
      path: "",
      name: "main",
      component: dt,
      children: [
        {
          path: "",
          name: "Home",
          meta: { title: "首页 - Let Coding" },
          component: () =>
            I(
              () => import("./Home-CoeVi5xn.js"),
              __vite__mapDeps([0, 1, 2, 3, 4, 5, 6]),
            ),
        },
        {
          path: "/playground",
          name: "Playground",
          meta: { title: "在线代码编辑器 - Let Coding" },
          component: () =>
            I(
              () => import("./Playground-BfTZjueS.js"),
              __vite__mapDeps([7, 2, 1, 4, 5, 3, 8]),
            ),
        },
        {
          path: "/learn",
          name: "Learn",
          meta: { title: "学习资源 - Let Coding", requiresAuth: !0 },
          component: () =>
            I(
              () => import("./Learn-Dk4tAsZi.js"),
              __vite__mapDeps([9, 1, 2, 10, 11, 4, 5, 3, 12, 13, 14]),
            ),
        },
        {
          path: "/announcements",
          name: "Announcements",
          meta: { title: "公告 - Let Coding" },
          component: () =>
            I(
              () => import("./Announcements-C8x2hTQo.js"),
              __vite__mapDeps([15, 1, 2, 10, 11, 4, 5, 3, 12, 13, 16]),
            ),
        },
      ],
    },
    {
      path: "/login",
      name: "login",
      meta: { title: "登录 - Let Coding" },
      component: () =>
        I(
          () => import("./Login-CWKUFn9f.js"),
          __vite__mapDeps([17, 2, 1, 3, 4, 5, 18]),
        ),
    },
    {
      path: "/auth/callback",
      name: "authCallback",
      meta: { title: "登录中 - Let Coding" },
      component: () =>
        I(
          () => import("./AuthCallback-Bm3huQjk.js"),
          __vite__mapDeps([19, 2, 1, 3, 4, 5]),
        ),
    },
    {
      path: "/admin",
      name: "admin",
      component: xt,
      meta: { title: "管理后台 - Let Coding" },
      children: [
        { path: "", redirect: "/admin/dashboard" },
        {
          path: "dashboard",
          name: "AdminDashboard",
          meta: { title: "仪表盘 - Let Coding 管理后台" },
          component: () =>
            I(
              () => import("./Dashboard-Bc5JRRr4.js"),
              __vite__mapDeps([20, 1, 2, 3, 4, 5, 21]),
            ),
        },
        {
          path: "users",
          name: "AdminUsers",
          meta: { title: "用户管理 - Let Coding 管理后台" },
          component: () =>
            I(
              () => import("./Users-QdQaWben.js"),
              __vite__mapDeps([22, 2, 1, 3, 4, 5, 23]),
            ),
        },
      ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  ke = Ie({ history: Oe(), routes: Et });
ke.beforeEach((e, s, o) => {
  if (((document.title = e.meta.title || "Let Coding"), e.meta.requiresAuth)) {
    const i = z();
    if (!i.isAuthenticated) {
      (i.startOAuthLogin("iOSClub", e.fullPath, !0), o(!1));
      return;
    }
  }
  o();
});
const Lt = Te(),
  ae = Pe(Fe);
ae.use(Lt);
ae.use(ke);
ae.mount("#app");
export { ue as _, ye as a, _e as b, $ as c, z as u };
