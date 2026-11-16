// Loads MJxPrep.js into a page that mimics an Open edX CAPA problem, with the
// real MathJax 2.7.5 (edx-platform before openedx/edx-platform#33555) or 4.1.2
// (after it). MathJax is requested from the same CDN URLs edx-platform uses and
// served from node_modules, so the test runs offline.
//
// MJXPREP_JS=/path/to/MJxPrep.js runs it against another copy, e.g. a course's.
const fs = require("node:fs");
const path = require("node:path");
const { test, expect } = require("@playwright/test");

const MJXPREP_JS =
  process.env.MJXPREP_JS || path.join(__dirname, "..", "MJxPrep.js");
const NODE_MODULES = path.join(__dirname, "..", "node_modules");
const LMS = "http://lms.test";

// Answers saved in textline problems before the page loads. Each needs either
// MJxPrep's preprocessor or one of its AsciiMath definitions to render right.
const TEXTLINE_ANSWERS = [
  { value: "hbar", mathml: /ℏ|&#x210F;/i },
  { value: "arctanh(x)", mathml: /<mi[^>]*>arctanh<\/mi>/ },
  { value: "adj(A)", mathml: /†|&#x2020;/i },
  { value: "trans(A)", mathml: /<msup[^>]*>[^]*?>A<\/mi>[^]*?>T<\/mi>[^]*?<\/msup>/ },
];
// formulaequationinput has no preprocessor; on MathJax 4 CAPA previews it
// through AsciiMath too, so it still needs MJxPrep's definitions.
const FORMULA_ANSWER = { id: "9", value: "arcsech(x)", mathml: /<mi[^>]*>arcsech<\/mi>/ };

// common/templates/mathjax_include.html before and after #33555, trimmed to
// the parts that affect AsciiMath previews.
const MATHJAX = {
  2: {
    version: "2.7.5",
    head: `
      <script type="text/x-mathjax-config">
        MathJax.Hub.Config({
          messageStyle: "none",
          tex2jax: {
            inlineMath: [["\\\\(","\\\\)"], ["[mathjaxinline]","[/mathjaxinline]"]],
            displayMath: [["\\\\[","\\\\]"], ["[mathjax]","[/mathjax]"]]
          }
        });
      </script>
      <script src="https://cdn.jsdelivr.net/npm/mathjax@2.7.5/MathJax.js?config=TeX-MML-AM_SVG"></script>`,
    started: "new Promise(function (resolve) { MathJax.Hub.Queue(resolve); })",
    // xmodule/js/src/capa/display.js bind() and refreshMath before #33555.
    // formulaequationinput previews went through an AJAX previewer then.
    capa: `
      function refreshMath(event, element) {
        element = element || event.target;
        var elid = element.id.replace(/^input_/, "");
        var jax = MathJax.Hub.getAllJax("display_" + elid)[0];
        if (!jax) { return; }
        var eqn = element.value;
        var preprocessor = preprocessorFor(element);
        if (preprocessor) { eqn = preprocessor(eqn); }
        MathJax.Hub.Queue(["Text", jax, eqn], [function () {
          document.getElementById(element.id + "_dynamath").value = jax.root.toMathML("");
        }]);
      }
      function bindProblem() {
        document.querySelectorAll("input.math").forEach(function (element) {
          element.addEventListener("keyup", refreshMath);
          MathJax.Hub.Queue([refreshMath, null, element]);
        });
      }`,
  },
  4: {
    version: "4.1.2",
    head: `
      <script>
        window.MathJax = {
          tex: {
            inlineMath: [["\\\\(","\\\\)"], ["[mathjaxinline]","[/mathjaxinline]"]],
            displayMath: [["\\\\[","\\\\]"], ["[mathjax]","[/mathjax]"]],
            autoload: { color: [], colorv2: ["color"] },
            packages: { "[+]": ["noerrors"] }
          },
          options: { ignoreHtmlClass: "tex2jax_ignore", processHtmlClass: "tex2jax_process" },
          loader: { load: ["input/asciimath", "[tex]/noerrors"] }
        };
      </script>
      <script id="MathJax-script" src="https://cdn.jsdelivr.net/npm/mathjax@4.1.2/tex-mml-chtml.js"></script>`,
    started: "MathJax.startup.promise",
    // xmodule/js/src/capa/display.js bind() and refreshMath after #33555
    capa: `
      function typesetReady() {
        return MathJax.startup && MathJax.startup.promise &&
          typeof MathJax.typesetPromise === "function";
      }
      function refreshMath(event, element) {
        element = element || event.target;
        if (!typesetReady() || typeof MathJax.typesetClear !== "function") { return; }
        var elid = element.id.replace(/^input_/, "");
        var math = document.getElementById("display_" + elid) ||
          document.getElementById(element.id + "_preview");
        if (!math) { return; }
        var eqn = element.value;
        var preprocessor = preprocessorFor(element);
        if (preprocessor) { eqn = preprocessor(eqn); }
        MathJax.typesetClear([math]);
        math.textContent = "\`" + eqn + "\`";
        MathJax.typesetPromise([math]).then(function () {
          var jax = MathJax.startup.document.getMathItemsWithin(math)[0];
          var dynamath = document.getElementById(element.id + "_dynamath");
          if (jax && dynamath) { dynamath.value = MathJax.startup.toMML(jax.root); }
        });
      }
      function bindProblem() {
        document.querySelectorAll("input.math, .formulaequationinput input").forEach(function (element) {
          element.addEventListener("keyup", refreshMath);
          if (typesetReady()) {
            MathJax.startup.promise.then(function () { refreshMath(null, element); });
          }
        });
      }`,
  },
};

// xmodule/capa/templates/textline.html with do_math and a preprocessor
function textline(id, value) {
  return `
    <div id="inputtype_${id}" class="text-input-dynamath capa_inputtype textline">
      <div class="text-input-dynamath_data" data-preprocessor="MJxPrep"></div>
      <input type="text" class="math" name="input_${id}" id="input_${id}" value="${value}" />
      <div id="display_${id}" class="equation">\`{::}\`</div>
      <textarea style="display:none" id="input_${id}_dynamath" name="input_${id}_dynamath"></textarea>
    </div>`;
}

// xmodule/capa/templates/formulaequationinput.html
function formulaequationinput(id, value) {
  return `
    <div id="formulaequationinput_${id}" class="inputtype formulaequationinput">
      <input type="text" name="input_${id}" id="input_${id}" data-input-id="${id}" value="${value}" />
      <div id="input_${id}_preview" class="equation">\\(\\)</div>
    </div>`;
}

// A course's MJxPrepCustom.js, as docs/grading_math/renderer.md describes
const COURSE_CONFIG = `
  window.MJxPrepOptions = { conj_as_star: true };
  window.MJxPrepCustom = {
    symbols: [{ input: "ell", tag: "mo", output: "\\u2113", tex: null, ttype: "CONST" }],
    post: function (eqn) { return eqn.replace(/nfact/g, "n!"); }
  };`;
const COURSE_CONFIG_ANSWERS = [
  { value: "ell", mathml: /ℓ|&#x2113;/i },
  { value: "conj(z)", mathml: /∗|&#x2217;/i },
  { value: "nfact", mathml: /<mo[^>]*>!<\/mo>/ },
];

function textlineAnswers(config) {
  return config ? [...TEXTLINE_ANSWERS, ...COURSE_CONFIG_ANSWERS] : TEXTLINE_ANSWERS;
}

// CAPA's JavascriptLoader runs the problem's scripts and then binds the
// problem. "early" does that while MathJax is still loading, "late" once
// MathJax has finished its first typeset. config puts the course's config
// file before or after MJxPrep.js, or leaves it out.
function unitPage(major, timing, config) {
  const mathjax = MATHJAX[major];
  const scripts = { before: ["MJxPrepCustom.js", "MJxPrep.js"], after: ["MJxPrep.js", "MJxPrepCustom.js"] }[config] || ["MJxPrep.js"];
  const load =
    timing === "early"
      ? scripts.map((name) => `<script src="/static/${name}"></script>`).join("") +
        `<script>bindProblem();</script>`
      : `<script>
          function loadInOrder(names, done) {
            if (names.length === 0) { return done(); }
            var script = document.createElement("script");
            script.src = "/static/" + names[0];
            script.onload = function () { loadInOrder(names.slice(1), done); };
            document.body.appendChild(script);
          }
          window.addEventListener("load", function () {
            ${mathjax.started}.then(function () {
              loadInOrder(${JSON.stringify(scripts)}, bindProblem);
            });
          });
        </script>`;
  return `<!DOCTYPE html>
    <html><head><meta charset="utf-8">${mathjax.head}</head>
    <body>
      ${textlineAnswers(config).map((answer, i) => textline(i + 1, answer.value)).join("\n")}
      ${formulaequationinput(FORMULA_ANSWER.id, FORMULA_ANSWER.value)}
      <script>
        function preprocessorFor(element) {
          var inputtype = element.closest(".text-input-dynamath");
          if (!inputtype) { return null; }
          var data = inputtype.querySelector(".text-input-dynamath_data");
          var cls = window[data.dataset.preprocessor];
          return cls ? new cls().fn : null;
        }
        ${mathjax.capa}
      </script>
      ${load}
    </body></html>`;
}

const FONT_PACKAGE = ["mathjax4/node_modules/@mathjax/mathjax-newcm-font", "@mathjax/mathjax-newcm-font"]
  .map((pkg) => path.join(NODE_MODULES, pkg))
  .find((dir) => fs.existsSync(dir));

// Map CDN requests onto the installed packages; anything else is recorded and
// refused so the test can't silently depend on the network.
async function serveLocally(page, major, timing, config, unrouted) {
  const cdnPackages = [
    [/^\/npm\/mathjax@2\.7\.5\/(.*)$/, path.join(NODE_MODULES, "mathjax2")],
    [/^\/npm\/mathjax@4\.1\.2\/(.*)$/, path.join(NODE_MODULES, "mathjax4")],
    [/^\/npm\/@mathjax\/mathjax-newcm-font@[^/]+\/(.*)$/, FONT_PACKAGE],
  ];
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.origin === LMS) {
      if (url.pathname === "/unit") {
        return route.fulfill({ contentType: "text/html", body: unitPage(major, timing, config) });
      }
      if (url.pathname === "/static/MJxPrep.js") {
        return route.fulfill({ path: MJXPREP_JS, contentType: "application/javascript" });
      }
      if (url.pathname === "/static/MJxPrepCustom.js") {
        return route.fulfill({ body: COURSE_CONFIG, contentType: "application/javascript" });
      }
    }
    if (url.host === "cdn.jsdelivr.net") {
      for (const [pattern, dir] of cdnPackages) {
        const match = url.pathname.match(pattern);
        const file = match && path.join(dir, match[1]);
        if (file && fs.existsSync(file)) {
          return route.fulfill({ path: file });
        }
      }
    }
    unrouted.push(url.href);
    return route.abort();
  });
}

async function previewMathML(page, inputId) {
  return page.evaluate((id) => {
    const preview = document.getElementById(`input_${id}_preview`);
    const item = MathJax.startup.document.getMathItemsWithin(preview)[0];
    return item ? MathJax.startup.toMML(item.root) : "";
  }, inputId);
}

const LOAD_ORDERS = ["early", "late"].flatMap((timing) =>
  [null, "before", "after"].map((config) => ({ timing, config })),
);

for (const major of [2, 4]) {
  for (const { timing, config } of LOAD_ORDERS) {
    const configName = config ? `, course config loaded ${config} it` : "";
    test(`renders saved answers with MJxPrep definitions on MathJax ${MATHJAX[major].version}, MJxPrep loaded ${timing}${configName}`, async ({ page }) => {
      const errors = [];
      const mjxprepLogs = [];
      const unrouted = [];
      page.on("pageerror", (err) => errors.push(err.message));
      page.on("console", (msg) => {
        // MathJax warns when a component's version doesn't match its core,
        // which would mean the test isn't running what the LMS serves.
        if (msg.type() === "error" || /version in use is/.test(msg.text())) {
          errors.push(msg.text());
        }
        if (msg.text().startsWith("MITx Grading Library")) {
          mjxprepLogs.push(`${msg.type()}: ${msg.text()}`);
        }
      });
      // Track MJxPrep's AsciiMath poll so the test can check it stops
      await page.addInitScript(() => {
        const polls = { started: 0, active: new Set() };
        const setInterval = window.setInterval;
        const clearInterval = window.clearInterval;
        window.setInterval = function (fn, ...rest) {
          const id = setInterval.call(window, fn, ...rest);
          if (fn && fn.name === "updateMathJax") {
            polls.started += 1;
            polls.active.add(id);
          }
          return id;
        };
        window.clearInterval = function (id) {
          polls.active.delete(id);
          return clearInterval.call(window, id);
        };
        window.__mjxprepPolls = () => ({ started: polls.started, active: polls.active.size });
      });
      await serveLocally(page, major, timing, config, unrouted);

      await page.goto(`${LMS}/unit`);

      for (const [i, answer] of textlineAnswers(config).entries()) {
        await expect
          .poll(() => page.inputValue(`#input_${i + 1}_dynamath`), {
            message: `preview MathML for saved answer ${answer.value}`,
          })
          .toMatch(answer.mathml);
      }
      if (major === 4) {
        await expect
          .poll(() => previewMathML(page, FORMULA_ANSWER.id), {
            message: `formulaequationinput preview MathML for ${FORMULA_ANSWER.value}`,
          })
          .toMatch(FORMULA_ANSWER.mathml);
      }
      expect(errors).toEqual([]);
      expect(unrouted).toEqual([]);
      expect(await page.evaluate(() => window.__mjxprepPolls())).toEqual({ started: 1, active: 0 });
      expect(mjxprepLogs).toEqual([
        expect.stringMatching(
          `^log: MITx Grading Library \\(MJxPrep.js \\d+\\.\\d+\\.\\d+\\): ` +
          `Updated AsciiMath renderer definitions \\(MathJax ${MATHJAX[major].version}\\)$`,
        ),
      ]);
    });
  }
}
