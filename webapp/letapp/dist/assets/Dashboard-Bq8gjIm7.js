import { I as l } from "./vendor-icons-DUK5cEDW.js";
import {
  h as g,
  J as o,
  K as e,
  F as c,
  V as i,
  Q as d,
  O as s,
  L as r,
  l as p,
  N as n,
  E as m,
} from "./vendor-vue-D0UmDA62.js";
import { a as v } from "./index-CHWsF88q.js";
import "./vendor-naive-Co-etydz.js";
import "./vendor-monaco-CQJlpWvK.js";
const _ = { class: "space-y-6" },
  k = { class: "grid gap-6 md:grid-cols-2 xl:grid-cols-4" },
  f = { class: "flex items-center justify-between" },
  h = { class: "text-sm font-bold text-slate-500 dark:text-slate-400" },
  y = { class: "mt-2 text-3xl font-black" },
  w = {
    class:
      "mt-3 flex items-center gap-1 text-sm font-bold text-emerald-600 dark:text-emerald-300",
  },
  j = { class: "grid gap-6 xl:grid-cols-2" },
  A = { class: "admin-card" },
  C = { class: "space-y-3" },
  N = { class: "flex items-center gap-3" },
  V = {
    class:
      "grid h-11 w-11 place-items-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300",
  },
  B = { class: "flex items-center gap-2" },
  D = { class: "font-black" },
  E = {
    class:
      "rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  },
  I = { class: "text-sm text-slate-500 dark:text-slate-400" },
  J = { class: "admin-card" },
  L = { class: "space-y-3" },
  F = { class: "flex items-center gap-3" },
  S = {
    class:
      "grid h-11 w-11 place-items-center rounded-2xl bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300",
  },
  z = { class: "flex items-center gap-2" },
  K = { class: "font-black" },
  O = {
    class:
      "rounded-full bg-violet-100 px-2 py-0.5 text-xs font-bold text-violet-700 dark:bg-violet-950 dark:text-violet-300",
  },
  P = { class: "text-sm text-slate-500 dark:text-slate-400" },
  Q = g({
    __name: "Dashboard",
    setup(T) {
      const x = [
          {
            title: "总用户数",
            value: 1250,
            icon: "material-symbols:people",
            color:
              "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300",
            trend: "+15%",
          },
          {
            title: "活跃用户",
            value: 890,
            icon: "material-symbols:person",
            color:
              "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
            trend: "+8%",
          },
          {
            title: "代码执行次数",
            value: 5680,
            icon: "material-symbols:code",
            color:
              "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300",
            trend: "+22%",
          },
          {
            title: "学习资源数",
            value: 120,
            icon: "material-symbols:school",
            color:
              "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
            trend: "+5%",
          },
        ],
        u = [
          {
            id: 1,
            name: "admin",
            email: "admin@example.com",
            role: "管理员",
            status: "active",
            joined: "2026-06-01",
          },
          {
            id: 2,
            name: "user1",
            email: "user1@example.com",
            role: "普通用户",
            status: "active",
            joined: "2026-06-03",
          },
          {
            id: 3,
            name: "user2",
            email: "user2@example.com",
            role: "普通用户",
            status: "inactive",
            joined: "2026-06-05",
          },
          {
            id: 4,
            name: "guest1",
            email: "guest1@example.com",
            role: "访客",
            status: "active",
            joined: "2026-06-08",
          },
        ],
        b = [
          {
            id: 1,
            user: "user1",
            language: "JavaScript",
            status: "success",
            executedAt: "2026-06-12 14:30",
          },
          {
            id: 2,
            user: "user2",
            language: "Python",
            status: "error",
            executedAt: "2026-06-12 14:25",
          },
          {
            id: 3,
            user: "admin",
            language: "Java",
            status: "success",
            executedAt: "2026-06-12 14:20",
          },
          {
            id: 4,
            user: "guest1",
            language: "C++",
            status: "success",
            executedAt: "2026-06-12 14:15",
          },
        ];
      return (U, a) => (
        d(),
        o("div", _, [
          a[3] ||
            (a[3] = e(
              "div",
              null,
              [
                e(
                  "h1",
                  { class: "text-3xl font-black tracking-tight" },
                  "仪表盘",
                ),
                e(
                  "p",
                  { class: "mt-2 text-slate-600 dark:text-slate-300" },
                  "欢迎来到 Let Coding 管理后台。",
                ),
              ],
              -1,
            )),
          e("div", k, [
            (d(),
            o(
              c,
              null,
              i(x, (t) =>
                e("article", { key: t.title, class: "admin-card" }, [
                  e("div", f, [
                    e("div", null, [
                      e("p", h, s(t.title), 1),
                      e("h3", y, s(t.value), 1),
                      e("div", w, [
                        r(n(l), {
                          icon: "material-symbols:trending-up",
                          class: "h-4 w-4",
                        }),
                        p(" " + s(t.trend) + " ", 1),
                        a[0] ||
                          (a[0] = e(
                            "span",
                            { class: "font-medium text-slate-400" },
                            "较上周",
                            -1,
                          )),
                      ]),
                    ]),
                    e(
                      "div",
                      {
                        class: m([
                          "grid h-14 w-14 place-items-center rounded-2xl",
                          t.color,
                        ]),
                      },
                      [
                        r(n(l), { icon: t.icon, class: "h-7 w-7" }, null, 8, [
                          "icon",
                        ]),
                      ],
                      2,
                    ),
                  ]),
                ]),
              ),
              64,
            )),
          ]),
          e("div", j, [
            e("section", A, [
              a[1] ||
                (a[1] = e(
                  "div",
                  { class: "mb-4 flex items-center justify-between" },
                  [
                    e("h2", { class: "text-xl font-black" }, "最近用户"),
                    e(
                      "button",
                      {
                        class:
                          "text-sm font-bold text-cyan-600 dark:text-cyan-300",
                      },
                      "查看全部",
                    ),
                  ],
                  -1,
                )),
              e("div", C, [
                (d(),
                o(
                  c,
                  null,
                  i(u, (t) =>
                    e(
                      "div",
                      {
                        key: t.id,
                        class:
                          "flex items-center justify-between rounded-2xl p-3 transition hover:bg-slate-50 dark:hover:bg-slate-800",
                      },
                      [
                        e("div", N, [
                          e("div", V, [
                            r(n(l), {
                              icon: "material-symbols:person",
                              class: "h-6 w-6",
                            }),
                          ]),
                          e("div", null, [
                            e("div", B, [
                              e("span", D, s(t.name), 1),
                              e("span", E, s(t.role), 1),
                            ]),
                            e("p", I, s(t.email), 1),
                          ]),
                        ]),
                        e(
                          "span",
                          {
                            class: m([
                              "rounded-full px-2.5 py-1 text-xs font-black",
                              t.status === "active"
                                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
                            ]),
                          },
                          s(t.status === "active" ? "活跃" : "未激活"),
                          3,
                        ),
                      ],
                    ),
                  ),
                  64,
                )),
              ]),
            ]),
            e("section", J, [
              a[2] ||
                (a[2] = e(
                  "div",
                  { class: "mb-4 flex items-center justify-between" },
                  [
                    e("h2", { class: "text-xl font-black" }, "最近代码执行"),
                    e(
                      "button",
                      {
                        class:
                          "text-sm font-bold text-cyan-600 dark:text-cyan-300",
                      },
                      "查看全部",
                    ),
                  ],
                  -1,
                )),
              e("div", L, [
                (d(),
                o(
                  c,
                  null,
                  i(b, (t) =>
                    e(
                      "div",
                      {
                        key: t.id,
                        class:
                          "flex items-center justify-between rounded-2xl p-3 transition hover:bg-slate-50 dark:hover:bg-slate-800",
                      },
                      [
                        e("div", F, [
                          e("div", S, [
                            r(n(l), {
                              icon: "material-symbols:code",
                              class: "h-6 w-6",
                            }),
                          ]),
                          e("div", null, [
                            e("div", z, [
                              e("span", K, s(t.user), 1),
                              e("span", O, s(t.language), 1),
                            ]),
                            e("p", P, s(t.executedAt), 1),
                          ]),
                        ]),
                        e(
                          "span",
                          {
                            class: m([
                              "rounded-full px-2.5 py-1 text-xs font-black",
                              t.status === "success"
                                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                                : "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
                            ]),
                          },
                          s(t.status === "success" ? "成功" : "失败"),
                          3,
                        ),
                      ],
                    ),
                  ),
                  64,
                )),
              ]),
            ]),
          ]),
        ])
      );
    },
  }),
  W = v(Q, [["__scopeId", "data-v-6836a915"]]);
export { W as default };
