(function () {
  var el = document.getElementById("map");
  if (!el || typeof L === "undefined") return;

  var points = window.__points || [];
  var tiles = window.__tiles || {
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "&copy; OpenStreetMap contributors",
  };
  var map = L.map(el, { scrollWheelZoom: true, worldCopyJump: true });
  L.tileLayer(tiles.url, { maxZoom: 19, attribution: tiles.attribution }).addTo(map);

  var bounds = [];
  points.forEach(function (p) {
    var color = p.kind === "destination" ? "#e0673f" : "#3f8fe0";
    var popup = p.url
      ? "<strong>" + p.label + "</strong><br><a href=\"" + p.url + "\">Open →</a>"
      : "<strong>" + p.label + "</strong>";
    var marker = L.circleMarker([p.lat, p.lon], {
      radius: p.kind === "destination" ? 8 : 6,
      color: color,
      weight: 2,
      fillColor: color,
      fillOpacity: p.kind === "destination" ? 0.85 : 0.6,
    }).bindPopup(popup);
    marker.addTo(map);
    bounds.push([p.lat, p.lon]);
  });

  if (bounds.length === 1) {
    map.setView(bounds[0], 8);
  } else if (bounds.length > 1) {
    map.fitBounds(bounds, { padding: [40, 40] });
  }
})();
