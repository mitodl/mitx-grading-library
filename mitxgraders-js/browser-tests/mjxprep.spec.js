// Loads MJxPrep.js into a page that mimics an Open edX CAPA textline problem,
// with the real MathJax 2.7.5 (edx-platform before openedx/edx-platform#33555)
// or 4.1.2 (after it). MathJax is requested from the same CDN URLs edx-platform
// uses and served from node_modules, so the test runs offline.
//
// MJXPREP_JS=/path/to/MJxPrep.js runs it against another copy, e.g. a course's.
const fs = require("node:fs");
const path = require("node:path");
const { test, expect } = require("@playwright/test");

const MJXPREP_JS =
  process.env.MJXPREP_JS || path.join(__dirname, "..", "MJxPrep.js");
const NODE_MODULES = path.join(__dirname, "..", "node_modules");
const LMS = "http://lms.test";

// Answers saved in the problem before the page loads. Each needs either
// MJxPrep's preprocessor or one of its AsciiMath definitions to render right.
const ANSWERS = [
  { value: "hbar", mathml: /ℏ|&#x210F;/i },
  { value: "arctanh(x)", mathml: /<mi[^>]*>arctanh<\/mi>/ },
  { value: "adj(A)", mathml: /†|&#x2020;/i },
  { value: "trans(A)", mathml: /<msup[^>]*>[^]*?>A<\/mi>[^]*?>T<\/mi>[^]*?<\/msup>/ },
];

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
    // xmodule/js/src/capa/display.js Problem.prototype.refreshMath before #33555
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
      document.querySelectorAll("input.math").forEach(function (element) {
        element.addEventListener("keyup", refreshMath);
        MathJax.Hub.Queue([refreshMath, null, element]);
      });`,
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
    // xmodule/js/src/capa/display.js Problem.prototype.refreshMath after #33555
    capa: `
      function typesetReady() {
        return MathJax.startup && MathJax.startup.promise &&
          typeof MathJax.typesetPromise === "function";
      }
      function refreshMath(event, element) {
        element = element || event.target;
        if (!typesetReady() || typeof MathJax.typesetClear !== "function") { return; }
        var elid = element.id.replace(/^input_/, "");
        var math = document.getElementById("display_" + elid);
        var dynamath = document.getElementById(element.id + "_dynamath");
        var eqn = element.value;
        var preprocessor = preprocessorFor(element);
        if (preprocessor) { eqn = preprocessor(eqn); }
        MathJax.typesetClear([math]);
        math.textContent = "\`" + eqn + "\`";
        MathJax.typesetPromise([math]).then(function () {
          var jax = MathJax.startup.document.getMathItemsWithin(math)[0];
          if (jax) { dynamath.value = MathJax.startup.toMML(jax.root); }
        });
      }
      document.querySelectorAll("input.math, .formulaequationinput input").forEach(function (element) {
        element.addEventListener("keyup", refreshMath);
        if (typesetReady()) {
          MathJax.startup.promise.then(function () { refreshMath(null, element); });
        }
      });`,
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

function unitPage(major) {
  const mathjax = MATHJAX[major];
  return `<!DOCTYPE html>
    <html><head><meta charset="utf-8">${mathjax.head}</head>
    <body>
      ${ANSWERS.map((answer, i) => textline(i + 1, answer.value)).join("\n")}
      <!-- CAPA's JavascriptLoader runs the preprocessor script before it binds the problem -->
      <script src="/static/MJxPrep.js"></script>
      <script>
        function preprocessorFor(element) {
          var data = element.closest(".text-input-dynamath").querySelector(".text-input-dynamath_data");
          var cls = window[data.dataset.preprocessor];
          return cls ? new cls().fn : null;
        }
        ${mathjax.capa}
      </script>
    </body></html>`;
}

// Map CDN requests onto the installed packages; anything else is recorded and
// refused so the test can't silently depend on the network.
async function serveLocally(page, major, unrouted) {
  const cdnPackages = [
    [/^\/npm\/mathjax@2\.7\.5\/(.*)$/, "mathjax2"],
    [/^\/npm\/mathjax@4\.1\.2\/(.*)$/, "mathjax4"],
    [/^\/npm\/@mathjax\/mathjax-newcm-font@[^/]+\/(.*)$/, "@mathjax/mathjax-newcm-font"],
  ];
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.origin === LMS) {
      if (url.pathname === "/unit") {
        return route.fulfill({ contentType: "text/html", body: unitPage(major) });
      }
      if (url.pathname === "/static/MJxPrep.js") {
        return route.fulfill({ path: MJXPREP_JS, contentType: "application/javascript" });
      }
    }
    if (url.host === "cdn.jsdelivr.net") {
      for (const [pattern, pkg] of cdnPackages) {
        const match = url.pathname.match(pattern);
        const file = match && path.join(NODE_MODULES, pkg, match[1]);
        if (file && fs.existsSync(file)) {
          return route.fulfill({ path: file });
        }
      }
    }
    unrouted.push(url.href);
    return route.abort();
  });
}

for (const major of [2, 4]) {
  test(`renders saved answers with MJxPrep definitions on MathJax ${MATHJAX[major].version}`, async ({ page }) => {
    const errors = [];
    const mjxprepLogs = [];
    const unrouted = [];
    page.on("pageerror", (err) => errors.push(err.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") { errors.push(msg.text()); }
      if (msg.text().startsWith("MITx Grading Library")) {
        mjxprepLogs.push(`${msg.type()}: ${msg.text()}`);
      }
    });
    // Track MJxPrep's AsciiMath poll so the test can check it stops
    await page.addInitScript(() => {
      const polls = new Set();
      const setInterval = window.setInterval;
      const clearInterval = window.clearInterval;
      window.setInterval = function (fn, ...rest) {
        const id = setInterval.call(window, fn, ...rest);
        if (fn && fn.name === "updateMathJax") { polls.add(id); }
        return id;
      };
      window.clearInterval = function (id) {
        polls.delete(id);
        return clearInterval.call(window, id);
      };
      window.__mjxprepActivePolls = () => polls.size;
    });
    await serveLocally(page, major, unrouted);

    await page.goto(`${LMS}/unit`);

    for (const [i, answer] of ANSWERS.entries()) {
      await expect
        .poll(() => page.inputValue(`#input_${i + 1}_dynamath`), {
          message: `preview MathML for saved answer ${answer.value}`,
        })
        .toMatch(answer.mathml);
    }
    expect(errors).toEqual([]);
    expect(unrouted).toEqual([]);
    expect(await page.evaluate(() => window.__mjxprepActivePolls())).toBe(0);
    expect(mjxprepLogs).toEqual([
      expect.stringMatching(
        `^log: MITx Grading Library \\(MJxPrep.js \\d+\\.\\d+\\.\\d+\\): ` +
        `Updated AsciiMath renderer definitions \\(MathJax ${MATHJAX[major].version}\\)$`,
      ),
    ]);
  });
}
