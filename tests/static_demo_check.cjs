const {
  parseInput,
  analyze,
  formatCurrent,
  formatPower,
  formatVoltage,
  statusMessage,
} = require("../demo.js");

const REFERENCE = {
  vcc: "12",
  r1: "47000",
  r2: "10000",
  rc: "2200",
  re: "1000",
  beta: "150",
  vbe: "0.7",
};

function calculate(raw) {
  const { data, errors } = parseInput(raw);
  if (Object.keys(errors).length > 0) {
    throw new Error(JSON.stringify(errors));
  }
  return analyze(data);
}

const reference = calculate(REFERENCE);
const cutoff = calculate({ ...REFERENCE, r2: "1000" });
const saturation = calculate({ ...REFERENCE, rc: "10000" });

console.log(
  JSON.stringify({
    region: reference.region,
    ib: reference.ib_a,
    ic: reference.ic_a,
    ie: reference.ie_a,
    vb: reference.vb_v,
    vc: reference.vc_v,
    ve: reference.ve_v,
    vce: reference.vce_v,
    pc: reference.pc_w,
    formatted: {
      vb: formatVoltage(reference.vb_v),
      ve: formatVoltage(reference.ve_v),
      vc: formatVoltage(reference.vc_v),
      vce: formatVoltage(reference.vce_v),
      ib: formatCurrent(reference.ib_a),
      ic: formatCurrent(reference.ic_a),
      ie: formatCurrent(reference.ie_a),
      pc: formatPower(reference.pc_w),
    },
    nano: formatCurrent(1.41e-9),
    cutoff: { region: cutoff.region, message: statusMessage(cutoff.region) },
    saturation: {
      region: saturation.region,
      message: statusMessage(saturation.region),
    },
  })
);
