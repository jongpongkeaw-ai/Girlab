(function (global) {
  "use strict";

  var FIELDS = ["vcc", "r1", "r2", "rc", "re", "beta", "vbe"];
  var VCE_SAT = 0.2;
  var DECIMAL = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;

  var STATUS = {
    active: "Active region approximation OK",
    cutoff: "Cutoff region \u2014 base current is zero or negative",
    saturation:
      "Saturation region \u2014 linear model is not valid (VCE \u2264 0.2 V)",
  };

  function parseInput(raw) {
    var errors = {};
    var values = {};

    FIELDS.forEach(function (field) {
      var text = String(raw[field] == null ? "" : raw[field]).trim();
      if (!text) {
        errors[field] = "Required";
        return;
      }
      if (!DECIMAL.test(text)) {
        errors[field] = /^[+-]?(inf(inity)?|nan)$/i.test(text)
          ? "Must be a finite number"
          : "Must be a number";
        return;
      }
      var value = Number(text);
      if (!Number.isFinite(value)) {
        errors[field] = "Must be a finite number";
        return;
      }
      values[field] = value;
    });

    FIELDS.forEach(function (field) {
      if (Object.prototype.hasOwnProperty.call(values, field) && values[field] <= 0) {
        errors[field] = "Must be greater than zero";
      }
    });

    if (values.vcc > 0 && Object.prototype.hasOwnProperty.call(values, "vbe")) {
      if (values.vbe >= values.vcc) {
        errors.vbe = "Must be less than VCC";
      }
    }

    if (Object.keys(errors).length > 0) {
      return { data: null, errors: errors };
    }
    return { data: values, errors: {} };
  }

  function analyze(data) {
    var vbb = (data.vcc * data.r2) / (data.r1 + data.r2);
    var rb = (data.r1 * data.r2) / (data.r1 + data.r2);
    var ib = (vbb - data.vbe) / (rb + (1 + data.beta) * data.re);
    var ic = data.beta * ib;
    var ie = (1 + data.beta) * ib;
    var ve = ie * data.re;
    var vc = data.vcc - ic * data.rc;
    var vce = vc - ve;
    var vb = data.vbe + ve;
    var pc = vce * ic;

    var warnings = [];
    var region;
    if (ib <= 0) {
      region = "cutoff";
      warnings.push("Transistor is in cutoff: base current is zero or negative.");
    } else if (vce <= VCE_SAT) {
      region = "saturation";
      warnings.push(
        "Transistor is in saturation: VCE is at or below VCE(sat); " +
          "the linear model is not valid."
      );
    } else {
      region = "active";
    }

    if (ib > 0 && data.vcc / (data.r1 + data.r2) < 10 * ib) {
      warnings.push(
        "Divider current is less than 10x IB; the bias point depends strongly on beta."
      );
    }

    return {
      ib_a: ib,
      ic_a: ic,
      ie_a: ie,
      vb_v: vb,
      vc_v: vc,
      ve_v: ve,
      vce_v: vce,
      pc_w: pc,
      region: region,
      warnings: warnings,
    };
  }

  function fixed(value, decimals) {
    var text = value.toFixed(decimals);
    if (text.charAt(0) === "-" && Number(text) === 0) {
      return text.slice(1);
    }
    return text;
  }

  function formatCurrent(amperes) {
    var magnitude = Math.abs(amperes);
    if (magnitude < 1e-6) {
      return fixed(amperes * 1e9, 2) + " nA";
    }
    if (magnitude < 1e-3) {
      return fixed(amperes * 1e6, 2) + " µA";
    }
    if (magnitude < 1) {
      return fixed(amperes * 1e3, 3) + " mA";
    }
    return fixed(amperes, 3) + " A";
  }

  function formatVoltage(volts) {
    return fixed(volts, 3) + " V";
  }

  function formatPower(watts) {
    if (Math.abs(watts) < 1) {
      return fixed(watts * 1e3, 2) + " mW";
    }
    return fixed(watts, 3) + " W";
  }

  function statusMessage(region) {
    return STATUS[region] || "";
  }

  function render(result) {
    var statusBox = document.getElementById("status-box");
    var output = document.getElementById("results-output");
    var empty = document.getElementById("results-empty");
    if (!statusBox || !output || !empty) {
      return;
    }

    statusBox.className = "status-box region-" + result.region;
    statusBox.textContent = statusMessage(result.region);

    document.getElementById("out-vb").textContent = formatVoltage(result.vb_v);
    document.getElementById("out-ve").textContent = formatVoltage(result.ve_v);
    document.getElementById("out-vc").textContent = formatVoltage(result.vc_v);
    document.getElementById("out-vce").textContent = formatVoltage(result.vce_v);
    document.getElementById("out-ib").textContent = formatCurrent(result.ib_a);
    document.getElementById("out-ic").textContent = formatCurrent(result.ic_a);
    document.getElementById("out-ie").textContent = formatCurrent(result.ie_a);
    document.getElementById("out-pc").textContent = formatPower(result.pc_w);

    var warnings = document.getElementById("out-warnings");
    warnings.textContent = "";
    result.warnings.forEach(function (warning) {
      var item = document.createElement("li");
      item.textContent = warning;
      warnings.appendChild(item);
    });

    empty.hidden = true;
    output.hidden = false;
  }

  function clearErrors() {
    var nodes = document.querySelectorAll("[data-error-for]");
    for (var i = 0; i < nodes.length; i += 1) {
      nodes[i].textContent = "";
    }
  }

  function showErrors(errors) {
    Object.keys(errors).forEach(function (field) {
      var node = document.querySelector('[data-error-for="' + field + '"]');
      if (node) {
        node.textContent = errors[field];
      }
    });
  }

  function init() {
    var form = document.getElementById("bias-form");
    if (!form) {
      return;
    }
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      clearErrors();

      var raw = {};
      FIELDS.forEach(function (field) {
        raw[field] = form.elements[field].value;
      });

      var parsed = parseInput(raw);
      if (Object.keys(parsed.errors).length > 0) {
        showErrors(parsed.errors);
        var output = document.getElementById("results-output");
        var empty = document.getElementById("results-empty");
        if (output && empty) {
          output.hidden = true;
          empty.hidden = false;
        }
        return;
      }

      render(analyze(parsed.data));
    });
  }

  var api = {
    FIELDS: FIELDS,
    VCE_SAT: VCE_SAT,
    parseInput: parseInput,
    analyze: analyze,
    formatCurrent: formatCurrent,
    formatVoltage: formatVoltage,
    formatPower: formatPower,
    statusMessage: statusMessage,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  global.BjtDemo = api;

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
