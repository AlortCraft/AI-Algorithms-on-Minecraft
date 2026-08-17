import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspace = "C:\\Users\\miste\\OneDrive\\Documentos\\minecraft_IA_Algorithms\\work\\presentation-v2";
const source = "C:\\Users\\miste\\OneDrive\\Documentos\\minecraft_IA_Algorithms\\work\\presentation-build\\final-for-qa.pptx";
const out = path.join(workspace, "template-inspect");

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

await fs.mkdir(path.join(out, "source-slides"), { recursive: true });
await fs.mkdir(path.join(out, "layouts"), { recursive: true });
const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
for (const [index, slide] of presentation.slides.items.entries()) {
  const padded = String(index + 1).padStart(2, "0");
  await writeBlob(path.join(out, "source-slides", `source-slide-${padded}.png`),
    await presentation.export({ slide, format: "png", scale: 1 }));
  await writeBlob(path.join(out, "layouts", `source-slide-${padded}.layout.json`),
    await presentation.export({ slide, format: "layout" }));
}
const inspection = await presentation.inspect({
  kind: "slide,textbox,shape,image,notes,layout",
  maxChars: 200000,
});
await fs.writeFile(path.join(out, "template-inspect.ndjson"), inspection.ndjson || "", "utf8");
await fs.writeFile(path.join(out, "template-manifest.json"), JSON.stringify({
  sourcePptx: source,
  slideCount: presentation.slides.items.length,
  fonts: ["Arial"],
  packageParts: { mediaCount: 1, slideXmlCount: presentation.slides.items.length },
}, null, 2));
console.log(path.join(out, "template-manifest.json"));
