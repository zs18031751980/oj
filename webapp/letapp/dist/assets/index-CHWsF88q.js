const __vite__mapDeps = (
  i,
  m = __vite__mapDeps,
  d = m.f ||
    (m.f = [
      "assets/Home-Bs74KEEN.js",
      "assets/vendor-icons-DUK5cEDW.js",
      "assets/vendor-vue-D0UmDA62.js",
      "assets/vendor-naive-Co-etydz.js",
      "assets/vendor-monaco-CQJlpWvK.js",
      "assets/vendor-monaco-Ck3IbhyB.css",
      "assets/Home-sp2UZ7Z6.css",
      "assets/Playground-Bg2zM9ah.js",
      "assets/Playground-DL-MPlTQ.css",
      "assets/Learn-MZQbw_O6.js",
      "assets/MarkdownComponent-Dj4guaHi.js",
      "assets/vendor-markdown-HlADSkmp.js",
      "assets/vendor-prism-DA50wpei.js",
      "assets/MarkdownComponent-UUfociu3.css",
      "assets/Learn-CoCjPmOR.css",
      "assets/Announcements-hc389CGk.js",
      "assets/Announcements-CvrKmVlL.css",
      "assets/Login-C-SP-b_2.js",
      "assets/Login-BODVWaZj.css",
      "assets/AuthCallback-irQ5SmPw.js",
      "assets/Dashboard-Bq8gjIm7.js",
      "assets/Dashboard-BXQvMu0t.css",
      "assets/Users-nZUAhf5U.js",
      "assets/Users-B3-PxQbJ.css",
    ]),
) => i.map((i) => d[i]);
var xe = Object.defineProperty;
var Se = (e, s, t) =>
  s in e
    ? xe(e, s, { enumerable: !0, configurable: !0, writable: !0, value: t })
    : (e[s] = t);
var Q = (e, s, t) => Se(e, typeof s != "symbol" ? s + "" : s, t);
import {
  _ as de,
  r as b,
  c as C,
  h as se,
  $ as me,
  d as he,
  S as G,
  N as d,
  P as x,
  a0 as K,
  Q as v,
  L as h,
  z as Ee,
  J as k,
  I as pe,
  K as n,
  E as R,
  M as D,
  F as X,
  V as q,
  O as j,
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
  p as Me,
  q as le,
  s as De,
  t as Ue,
} from "./vendor-naive-Co-etydz.js";
import { _ as I } from "./vendor-monaco-CQJlpWvK.js";
import { I as A } from "./vendor-icons-DUK5cEDW.js";
(function () {
  const s = document.createElement("link").relList;
  if (s && s.supports && s.supports("modulepreload")) return;
  for (const o of document.querySelectorAll('link[rel="modulepreload"]')) i(o);
  new MutationObserver((o) => {
    for (const l of o)
      if (l.type === "childList")
        for (const p of l.addedNodes)
          p.tagName === "LINK" && p.rel === "modulepreload" && i(p);
  }).observe(document, { childList: !0, subtree: !0 });
  function t(o) {
    const l = {};
    return (
      o.integrity && (l.integrity = o.integrity),
      o.referrerPolicy && (l.referrerPolicy = o.referrerPolicy),
      o.crossOrigin === "use-credentials"
        ? (l.credentials = "include")
        : o.crossOrigin === "anonymous"
          ? (l.credentials = "omit")
          : (l.credentials = "same-origin"),
      l
    );
  }
  function i(o) {
    if (o.ep) return;
    o.ep = !0;
    const l = t(o);
    fetch(o.href, l);
  }
})();
const fe = de("theme", () => {
    const e = "appThemePreference",
      s = b(localStorage.getItem(e) || "system"),
      t = b(window.matchMedia("(prefers-color-scheme: dark)").matches),
      i = (m) => {
        document.documentElement.classList.toggle("dark", m);
      },
      o = C({
        get() {
          return s.value === "dark" ? !0 : s.value === "light" ? !1 : t.value;
        },
        set(m) {
          ((s.value = m ? "dark" : "light"),
            localStorage.setItem(e, s.value),
            i(m));
        },
      }),
      l = C(() => (o.value ? Re : null));
    return {
      isDark: o,
      theme: l,
      userPreference: s,
      setThemePreference: (m) => {
        ((s.value = m), localStorage.setItem(e, m), i(o.value));
      },
      toggleTheme: () => {
        o.value = !o.value;
      },
      init: () => {
        (window
          .matchMedia("(prefers-color-scheme: dark)")
          .addEventListener("change", (y) => {
            ((t.value = y.matches), s.value === "system" && i(o.value));
          }),
          i(o.value));
      },
    };
  }),
  je = () => {
    const e = "https://ojapi.xauat.site".trim();
    if (e) return e;
    if (typeof window < "u") {
      const t = {
        "oj.xauat.site": "https://ojapi.xauat.site",
        "www.xauat.site": "https://ojapi.xauat.site",
        "xauat.site": "https://ojapi.xauat.site",
      }[window.location.hostname];
      if (t) return t;
    }
    return "http://localhost:6173";
  },
  _e = je(),
  oe = "auth_storage_mode";
class ge extends Error {
  constructor(t, i, o) {
    super(t);
    Q(this, "status");
    Q(this, "payload");
    ((this.name = "ApiError"), (this.status = i), (this.payload = o));
  }
}
const Z = () => (localStorage.getItem(oe) === "session" ? "session" : "local"),
  Ve = (e) => {
    localStorage.setItem(oe, e);
  },
  He = () => {
    localStorage.removeItem(oe);
  },
  P = (e = Z()) => (e === "session" ? sessionStorage : localStorage),
  Ke = () => P().getItem("access_token"),
  ze = async (e) => {
    if ((e.headers.get("content-type") || "").includes("application/json"))
      return e.json();
    const t = await e.text();
    return t ? { message: t } : {};
  };
async function $(e, s = {}) {
  const { skipAuth: t, headers: i, body: o, ...l } = s,
    p = new Headers(i);
  if (
    (o &&
      !(o instanceof FormData) &&
      !p.has("Content-Type") &&
      p.set("Content-Type", "application/json"),
    !t)
  ) {
    const m = Ke();
    m && !p.has("Authorization") && p.set("Authorization", `Bearer ${m}`);
  }
  const u = await fetch(`${_e}${e}`, { ...l, body: o, headers: p }),
    _ = await ze(u);
  if (!u.ok) {
    const m =
      typeof _ == "object" && _ && "error" in _
        ? String(_.error)
        : `请求失败，状态码 ${u.status}`;
    throw new ge(m, u.status, _);
  }
  return _;
}
const ee = "access_token",
  te = "refresh_token",
  U = "user_info",
  M = "oauth_login_remember",
  ve = "oauth_login_provider",
  be = "oauth_login_next",
  O = (e) =>
    Array.isArray(e) ? String(e[0] ?? "") : e == null ? "" : String(e),
  Be = (e, s = P()) => {
    const t = s.getItem(e);
    if (!t) return null;
    try {
      return JSON.parse(t);
    } catch {
      return (s.removeItem(e), null);
    }
  },
  ce = () => {
    for (const e of [localStorage, sessionStorage])
      (e.removeItem(ee), e.removeItem(te), e.removeItem(U));
    (sessionStorage.removeItem(M),
      sessionStorage.removeItem(ve),
      sessionStorage.removeItem(be),
      He());
  },
  Je = (e, s) => {
    const t = `${e} ${s}`.trim().toLowerCase();
    return t.includes("timeout") || t.includes("超时")
      ? "登录请求超时，请稍后重试。"
      : t.includes("会话创建失败")
        ? "第三方登录页面未能创建授权会话，请稍后重试或联系统一认证服务维护方。"
        : t.includes("access_denied") ||
            t.includes("denied") ||
            t.includes("拒绝")
          ? "你已取消授权，登录未完成。"
          : t.includes("missing") || t.includes("token") || t.includes("缺少")
            ? "登录回调缺少必要凭证，请重新发起登录。"
            : s || e || "登录失败，请稍后重试。";
  },
  z = de("auth", () => {
    const e = b(Z()),
      s = b(P(e.value).getItem(ee) || ""),
      t = b(P(e.value).getItem(te) || ""),
      i = b(Be(U, P(e.value))),
      o = b([]),
      l = b(!1),
      p = b(!1),
      u = C(() => !!s.value),
      _ = C(
        () =>
          i.value?.name || i.value?.username || i.value?.email || "已登录用户",
      ),
      m = C(() => i.value?.role || "member"),
      y = (a) => a instanceof ge && [400, 401, 403].includes(a.status),
      w = (a, r = {}) => {
        const g =
          r.storageMode ??
          (r.remember === void 0 ? Z() : r.remember ? "local" : "session");
        (ce(), Ve(g), (e.value = g));
        const f = P(g);
        ((s.value = a.access_token),
          (t.value = a.refresh_token),
          (i.value = a.user_info ?? null),
          f.setItem(ee, a.access_token),
          f.setItem(te, a.refresh_token),
          a.user_info
            ? f.setItem(U, JSON.stringify(a.user_info))
            : f.removeItem(U));
      },
      S = () => {
        ((s.value = ""),
          (t.value = ""),
          (i.value = null),
          (e.value = "local"),
          ce());
      },
      E = (a, r = "/", g = !0) => {
        sessionStorage.setItem(M, g ? "1" : "0");
        const f = r.startsWith("/") ? r : "/";
        (sessionStorage.setItem(ve, a), sessionStorage.setItem(be, f));
        const c = new URL(`${_e}/auth/login/${encodeURIComponent(a)}`);
        (c.searchParams.set("next", f), (window.location.href = c.toString()));
      },
      N = (a = "/", r = !0) => {
        E("github", a, r);
      },
      B = (a) => {
        const r = O(a.error);
        if (r) {
          const ke = O(a.error_description);
          throw (sessionStorage.removeItem(M), new Error(Je(r, ke)));
        }
        const g = O(a.access_token),
          f = O(a.refresh_token);
        if (!g || !f)
          throw (
            sessionStorage.removeItem(M),
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
        const ne = O(sessionStorage.getItem(M));
        sessionStorage.removeItem(M);
        const re = ne === "1" ? !0 : ne === "0" ? !1 : void 0;
        w(
          {
            access_token: g,
            refresh_token: f,
            expires_in: Number(O(a.expires_in) || 0),
            token_type: O(a.token_type) || "Bearer",
            user_info: c,
          },
          re === void 0 ? {} : { remember: re },
        );
      },
      L = async (a, r, g = !0) => {
        const f = await $("/auth/login/password", {
            method: "POST",
            skipAuth: !0,
            body: JSON.stringify({ identifier: a, password: r }),
          }),
          c = { ...f.tokens, user_info: f.tokens.user_info ?? f.user_info };
        return (w(c, { remember: g }), c);
      },
      J = async (a, r, g, f = !0) => {
        const c = await $(`/auth/login/${encodeURIComponent(a)}/password`, {
            method: "POST",
            skipAuth: !0,
            body: JSON.stringify({ identifier: r, password: g, remember: f }),
          }),
          T = { ...c.tokens, user_info: c.tokens.user_info ?? c.user_info };
        return (w(T, { remember: f }), T);
      },
      F = async () => {
        p.value = !0;
        try {
          const a = await $("/auth/providers", { skipAuth: !0 });
          return (
            (o.value = Array.isArray(a.providers) ? a.providers : []),
            o.value
          );
        } catch {
          return ((o.value = []), []);
        } finally {
          p.value = !1;
        }
      },
      V = async (a = {}) => {
        if (!s.value) return !1;
        l.value = !0;
        try {
          const r = await $("/auth/verify");
          return (
            r.user_info &&
              ((i.value = r.user_info),
              P(e.value).setItem(U, JSON.stringify(r.user_info))),
            r.valid
          );
        } catch (r) {
          return (a.clearOnFailure !== !1 && y(r) && S(), !1);
        } finally {
          l.value = !1;
        }
      },
      H = async () => {
        if (!t.value) return (S(), !1);
        try {
          const a = await $("/auth/refresh", {
            method: "POST",
            skipAuth: !0,
            body: JSON.stringify({ refresh_token: t.value }),
          });
          return (w(a, { storageMode: e.value }), !0);
        } catch (a) {
          return (y(a) && S(), !1);
        }
      };
    return {
      accessToken: s,
      refreshToken: t,
      userInfo: i,
      userRole: m,
      supportedProviders: o,
      isAuthenticated: u,
      isVerifying: l,
      isLoadingProviders: p,
      displayName: _,
      setSession: w,
      clearSession: S,
      startOAuthLogin: E,
      startGithubLogin: N,
      completeOAuthCallback: B,
      loginWithPassword: L,
      loginWithProviderPassword: J,
      loadSupportedProviders: F,
      verify: V,
      refresh: H,
      restoreSession: async () =>
        !s.value && !t.value
          ? !1
          : (s.value ? await V({ clearOnFailure: !1 }) : !1)
            ? !0
            : t.value
              ? H()
              : (S(), !1),
      logout: async () => {
        if (s.value)
          try {
            await $("/auth/logout", { method: "POST" });
          } catch {}
        S();
      },
    };
  }),
  Fe = se({
    __name: "App",
    setup(e) {
      const s = fe(),
        t = z(),
        { theme: i } = me(s),
        { init: o } = s;
      return (
        he(() => {
          (o(), t.restoreSession());
        }),
        (l, p) => {
          const u = K("router-view");
          return (
            v(),
            G(
              d(Ne),
              { theme: d(i) },
              {
                default: x(() => [
                  h(d($e), null, {
                    default: x(() => [
                      h(d(Me), null, { default: x(() => [h(u)]), _: 1 }),
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
  We = {
    class:
      "min-h-screen bg-slate-50 text-slate-950 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-50",
  },
  Ye = { class: "flex h-20 items-center justify-between gap-3 px-5" },
  Qe = { key: 0, class: "min-w-0" },
  Ge = { class: "flex-1 space-y-2 px-4 pb-6" },
  Xe = { key: 0, class: "truncate" },
  qe = { class: "border-t border-slate-200 p-4 dark:border-slate-800" },
  Ze = ["aria-label"],
  et = { key: 0, class: "text-sm font-bold" },
  tt = {
    class: "flex min-h-14 w-full min-w-0 items-center justify-between gap-3",
  },
  st = {
    class: "ml-auto flex min-w-0 items-center justify-end gap-2 sm:gap-3",
  },
  ot = { class: "relative shrink-0" },
  at = {
    key: 0,
    class:
      "absolute right-0 top-[calc(100%+0.75rem)] z-50 w-[min(18rem,calc(100vw-1.5rem))] rounded-[1.75rem] border border-slate-200 bg-white p-3 shadow-2xl shadow-slate-200/70 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/40",
  },
  nt = ["onClick"],
  rt = ["aria-label"],
  it = { class: "truncate" },
  lt = { class: "pt-20" },
  ct = 288,
  ut = 96,
  dt = se({
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
        t = pe(),
        i = fe(),
        o = z(),
        { isDark: l } = me(i),
        { toggleTheme: p } = i,
        u = b(!0),
        _ = b(!1),
        m = b(!1),
        y = b(!1),
        w = C(() => (u.value ? ct : ut)),
        S = C(() =>
          y.value
            ? { paddingLeft: `${w.value + 16}px`, paddingRight: "16px" }
            : void 0,
        ),
        E = C(() => ({
          ...(y.value ? { paddingLeft: `${w.value}px` } : {}),
          "--app-content-left": y.value ? `${w.value}px` : "0px",
        })),
        N = () => {
          y.value = window.innerWidth >= 768;
        },
        B = () => {
          u.value = !u.value;
        },
        L = () => {
          _.value = !1;
        },
        J = () => {
          (p(), L());
        },
        F = () => {
          (L(),
            o.startOAuthLogin("iOSClub", t.currentRoute.value.fullPath, !0));
        },
        V = async () => {
          (L(), await o.logout());
        },
        H = async (a) => {
          (L(), await t.push(a));
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
          const g = K("router-link"),
            f = K("router-view");
          return (
            v(),
            k("div", We, [
              h(
                d(le),
                { "has-sider": "", class: "min-h-screen bg-transparent" },
                {
                  default: x(() => [
                    n(
                      "aside",
                      {
                        class: R([
                          "fixed left-0 top-0 z-50 hidden h-screen flex-col border-r border-white/70 bg-white/88 shadow-2xl shadow-slate-200/60 backdrop-blur-2xl transition-all duration-300 dark:border-slate-800/80 dark:bg-slate-950/88 dark:shadow-black/30 md:flex",
                          u.value ? "w-72" : "w-24",
                        ]),
                      },
                      [
                        n("div", Ye, [
                          h(
                            g,
                            {
                              to: "/",
                              class:
                                "group flex min-w-0 items-center gap-3 overflow-hidden",
                              onClick: L,
                            },
                            {
                              default: x(() => [
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
                                    k("div", Qe, [
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
                                  : D("", !0),
                              ]),
                              _: 1,
                            },
                          ),
                        ]),
                        n("nav", Ge, [
                          (v(),
                          k(
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
                                  default: x(() => [
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
                                      ? (v(), k("span", Xe, j(c.label), 1))
                                      : D("", !0),
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
                        n("div", qe, [
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
                              onClick: B,
                            },
                            [
                              u.value
                                ? (v(), k("span", et, "收起"))
                                : D("", !0),
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
                            Ze,
                          ),
                        ]),
                      ],
                      2,
                    ),
                    h(d(le), null, {
                      default: x(() => [
                        h(
                          d(De),
                          {
                            class: R([
                              "fixed left-0 right-0 top-0 z-40 border-b border-white/60 bg-white/86 shadow-sm shadow-slate-200/40 backdrop-blur-2xl transition-all duration-300 dark:border-slate-800/80 dark:bg-slate-950/86 dark:shadow-black/20",
                              { "header-compact": m.value },
                            ]),
                          },
                          {
                            default: x(() => [
                              n(
                                "div",
                                {
                                  class:
                                    "h-auto min-h-20 w-full px-3 py-3 sm:px-4 lg:px-6",
                                  style: ie(S.value),
                                },
                                [
                                  n("div", tt, [
                                    h(
                                      g,
                                      {
                                        to: "/",
                                        class:
                                          "flex min-w-0 items-center gap-3 md:hidden",
                                        onClick: L,
                                      },
                                      {
                                        default: x(() => [
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
                                    n("div", st, [
                                      n("div", ot, [
                                        n(
                                          "button",
                                          {
                                            class: "icon-button",
                                            "aria-label": "打开导航菜单",
                                            onClick:
                                              r[0] ||
                                              (r[0] = Le(
                                                (c) => (_.value = !_.value),
                                                ["stop"],
                                              )),
                                          },
                                          [
                                            h(
                                              d(A),
                                              {
                                                icon: _.value
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
                                            default: x(() => [
                                              _.value
                                                ? (v(),
                                                  k("div", at, [
                                                    (v(),
                                                    k(
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
                                                              H(c.to),
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
                                                              j(c.label),
                                                              1,
                                                            ),
                                                          ],
                                                          8,
                                                          nt,
                                                        ),
                                                      ),
                                                      64,
                                                    )),
                                                  ]))
                                                : D("", !0),
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
                                          onClick: J,
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
                                        rt,
                                      ),
                                      d(o).isAuthenticated
                                        ? (v(),
                                          k(
                                            "button",
                                            {
                                              key: 1,
                                              class: "secondary-pill shrink-0",
                                              onClick: V,
                                            },
                                            [
                                              n(
                                                "span",
                                                it,
                                                "退出 " + j(d(o).displayName),
                                                1,
                                              ),
                                            ],
                                          ))
                                        : (v(),
                                          k(
                                            "button",
                                            {
                                              key: 0,
                                              class: "primary-pill shrink-0",
                                              onClick: F,
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
                          d(Ue),
                          {
                            class: "transition-all duration-300",
                            style: ie(E.value),
                          },
                          { default: x(() => [n("div", lt, [h(f)])]), _: 1 },
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
    const t = e.__vccOpts || e;
    for (const [i, o] of s) t[i] = o;
    return t;
  },
  mt = ye(dt, [["__scopeId", "data-v-fe417e00"]]),
  ht = {
    class:
      "min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50",
  },
  pt = {
    class:
      "sticky top-0 z-50 border-b border-slate-200 bg-white/85 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/85",
  },
  ft = { class: "flex h-16 items-center justify-between px-4" },
  _t = { class: "flex items-center gap-3" },
  gt = ["aria-label"],
  vt = { class: "flex items-center gap-3" },
  bt = {
    class:
      "hidden text-sm font-bold text-slate-500 dark:text-slate-400 md:inline",
  },
  yt = { class: "flex" },
  wt = { class: "p-4" },
  kt = ["onClick"],
  xt = { key: 0 },
  St = se({
    __name: "AdminLayout",
    setup(e) {
      const s = pe(),
        t = Ce(),
        i = z(),
        o = b(!0),
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
        p = C(() => t.path),
        u = () => {
          o.value = !o.value;
        },
        _ = (y) => {
          s.push(y);
        },
        m = async () => {
          (await i.logout(), s.push("/"));
        };
      return (y, w) => {
        const S = K("router-view");
        return (
          v(),
          k("div", ht, [
            n("header", pt, [
              n("div", ft, [
                n("div", _t, [
                  n(
                    "button",
                    {
                      class: "admin-icon-button",
                      "aria-label": o.value ? "收起侧边栏" : "展开侧边栏",
                      onClick: u,
                    },
                    [
                      h(
                        d(A),
                        {
                          icon: o.value
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
                    gt,
                  ),
                  w[0] ||
                    (w[0] = n(
                      "h1",
                      { class: "text-xl font-black" },
                      "Let Coding 管理后台",
                      -1,
                    )),
                ]),
                n("div", vt, [
                  n("span", bt, j(d(i).displayName), 1),
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
            n("div", yt, [
              n(
                "aside",
                {
                  class: R([
                    "fixed bottom-0 top-16 z-40 overflow-y-auto border-r border-slate-200 bg-white shadow-lg shadow-slate-200/50 transition-all duration-300 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20",
                    o.value ? "w-64" : "w-20",
                  ]),
                },
                [
                  n("nav", wt, [
                    (v(),
                    k(
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
                            onClick: (N) => _(E.route),
                          },
                          [
                            h(
                              d(A),
                              { icon: E.icon, class: "h-6 w-6 shrink-0" },
                              null,
                              8,
                              ["icon"],
                            ),
                            o.value
                              ? (v(), k("span", xt, j(E.title), 1))
                              : D("", !0),
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
                    o.value ? "ml-64" : "ml-20",
                  ]),
                },
                [h(S)],
                2,
              ),
            ]),
          ])
        );
      };
    },
  }),
  Et = ye(St, [["__scopeId", "data-v-864ff73a"]]),
  Lt = [
    {
      path: "",
      name: "main",
      component: mt,
      children: [
        {
          path: "",
          name: "Home",
          meta: { title: "首页 - Let Coding" },
          component: () =>
            I(
              () => import("./Home-Bs74KEEN.js"),
              __vite__mapDeps([0, 1, 2, 3, 4, 5, 6]),
            ),
        },
        {
          path: "/playground",
          name: "Playground",
          meta: { title: "在线代码编辑器 - Let Coding" },
          component: () =>
            I(
              () => import("./Playground-Bg2zM9ah.js"),
              __vite__mapDeps([7, 2, 1, 4, 5, 3, 8]),
            ),
        },
        {
          path: "/learn",
          name: "Learn",
          meta: { title: "学习资源 - Let Coding", requiresAuth: !0 },
          component: () =>
            I(
              () => import("./Learn-MZQbw_O6.js"),
              __vite__mapDeps([9, 1, 2, 10, 11, 4, 5, 3, 12, 13, 14]),
            ),
        },
        {
          path: "/announcements",
          name: "Announcements",
          meta: { title: "公告 - Let Coding" },
          component: () =>
            I(
              () => import("./Announcements-hc389CGk.js"),
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
          () => import("./Login-C-SP-b_2.js"),
          __vite__mapDeps([17, 2, 1, 3, 4, 5, 18]),
        ),
    },
    {
      path: "/auth/callback",
      name: "authCallback",
      meta: { title: "登录中 - Let Coding" },
      component: () =>
        I(
          () => import("./AuthCallback-irQ5SmPw.js"),
          __vite__mapDeps([19, 2, 1, 3, 4, 5]),
        ),
    },
    {
      path: "/admin",
      name: "admin",
      component: Et,
      meta: { title: "管理后台 - Let Coding" },
      children: [
        { path: "", redirect: "/admin/dashboard" },
        {
          path: "dashboard",
          name: "AdminDashboard",
          meta: { title: "仪表盘 - Let Coding 管理后台" },
          component: () =>
            I(
              () => import("./Dashboard-Bq8gjIm7.js"),
              __vite__mapDeps([20, 1, 2, 3, 4, 5, 21]),
            ),
        },
        {
          path: "users",
          name: "AdminUsers",
          meta: { title: "用户管理 - Let Coding 管理后台" },
          component: () =>
            I(
              () => import("./Users-nZUAhf5U.js"),
              __vite__mapDeps([22, 2, 1, 3, 4, 5, 23]),
            ),
        },
      ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  we = Ie({ history: Oe(), routes: Lt });
we.beforeEach((e, s, t) => {
  if (((document.title = e.meta.title || "Let Coding"), e.meta.requiresAuth)) {
    const i = z();
    if (!i.isAuthenticated) {
      (i.startOAuthLogin("iOSClub", e.fullPath, !0), t(!1));
      return;
    }
  }
  t();
});
const At = Te(),
  ae = Pe(Fe);
ae.use(At);
ae.use(we);
ae.mount("#app");
export { ue as _, ye as a, fe as b, $ as c, z as u };
