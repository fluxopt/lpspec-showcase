// A chart that keeps its place while it is redrawn.
//
// `resize` returns an empty element and draws into it once it knows its width,
// a frame later. When a slider redraws every chart at once, the page is
// briefly shorter by all of them, and the browser moves the reader to stay in
// range. `steady` holds the height the chart last had under its name until the
// new one is drawn, so the page never shrinks in between.
import {resize} from "observablehq:stdlib";

const heights = new Map();

export function steady(name, render) {
  const div = resize(render);
  if (heights.has(name)) div.style.minHeight = `${heights.get(name)}px`;
  new MutationObserver((_, observer) => {
    if (!div.firstChild) return;
    heights.set(name, div.firstChild.getBoundingClientRect().height);
    div.style.minHeight = "";
    observer.disconnect();
  }).observe(div, {childList: true});
  return div;
}
