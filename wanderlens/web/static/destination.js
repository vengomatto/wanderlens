(function () {
  var data = window.__dest;
  if (!data || typeof L === "undefined") return;

  var tiles = window.__tiles || {
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "&copy; OpenStreetMap contributors",
  };
  var markerColor = "#e0673f";
  var hasPoint = typeof data.lat === "number" && typeof data.lon === "number";

  function addBase(map) {
    L.tileLayer(tiles.url, { maxZoom: 19, attribution: tiles.attribution }).addTo(map);
  }

  function marker(map) {
    if (!hasPoint) return;
    L.circleMarker([data.lat, data.lon], {
      radius: 7,
      color: markerColor,
      weight: 2,
      fillColor: markerColor,
      fillOpacity: 0.9,
    })
      .addTo(map)
      .bindPopup("<strong>" + data.name + "</strong>");
  }

  var world = document.getElementById("world-map");
  if (world) {
    var wmap = L.map(world, { scrollWheelZoom: false, worldCopyJump: true });
    addBase(wmap);
    wmap.setView(hasPoint ? [data.lat, data.lon] : [20, 0], hasPoint ? 2 : 1);
    marker(wmap);
  }

  var region = document.getElementById("region-map");
  if (region) {
    var rmap = L.map(region, { scrollWheelZoom: true, worldCopyJump: true });
    addBase(rmap);
    marker(rmap);

    var bounds = hasPoint ? [[data.lat, data.lon]] : [];
    var geometry = null;
    if (data.region_geojson) {
      try {
        geometry = JSON.parse(data.region_geojson);
      } catch (e) {
        geometry = null;
      }
    }

    if (geometry && data.region_kind === "precise") {
      var layer = L.geoJSON(geometry, {
        style: { color: markerColor, weight: 2, fillColor: markerColor, fillOpacity: 0.18 },
      }).addTo(rmap);
      try {
        var box = layer.getBounds();
        bounds.push([box.getSouth(), box.getWest()], [box.getNorth(), box.getEast()]);
      } catch (e) {
        /* ignore */
      }
    } else if (hasPoint && data.region_kind === "approximate" && data.region_radius_km) {
      L.circle([data.lat, data.lon], {
        radius: data.region_radius_km * 1000,
        color: markerColor,
        weight: 2,
        dashArray: "6 6",
        fillColor: markerColor,
        fillOpacity: 0.12,
      }).addTo(rmap);
    }

    (data.pois || []).forEach(function (poi) {
      if (typeof poi.lat !== "number" || typeof poi.lon !== "number") return;
      L.circleMarker([poi.lat, poi.lon], {
        radius: 4,
        color: "#3f8fe0",
        weight: 1.5,
        fillColor: "#3f8fe0",
        fillOpacity: 0.8,
      })
        .addTo(rmap)
        .bindPopup("<strong>" + poi.name + "</strong>");
      bounds.push([poi.lat, poi.lon]);
    });

    if (bounds.length === 1) rmap.setView(bounds[0], 8);
    else if (bounds.length > 1) rmap.fitBounds(bounds, { padding: [40, 40] });
    else rmap.setView([20, 0], 1);
  }
})();
