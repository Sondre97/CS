// Render white Feather icons to PNG for use on BDO-red circles.
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");
const {
  FiLink2, FiTrendingDown, FiAlertTriangle, FiCpu, FiLifeBuoy, FiMessageCircle,
} = require("react-icons/fi");

const OUT = path.join(__dirname, "icons");
fs.mkdirSync(OUT, { recursive: true });

const icons = {
  "link-2": FiLink2,
  "trending-down": FiTrendingDown,
  "alert-triangle": FiAlertTriangle,
  "cpu": FiCpu,
  "life-buoy": FiLifeBuoy,
  "message-circle": FiMessageCircle,
};

(async () => {
  for (const [name, Comp] of Object.entries(icons)) {
    const svg = ReactDOMServer.renderToStaticMarkup(
      React.createElement(Comp, { color: "#FFFFFF", size: 256 })
    );
    await sharp(Buffer.from(svg), { density: 300 })
      .resize(256, 256)
      .png()
      .toFile(path.join(OUT, `${name}.png`));
    console.log("wrote icons/" + name + ".png");
  }
})();
