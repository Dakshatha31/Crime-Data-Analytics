/**
 * Leaflet Map Controller: Hotspots & Safe-Route Polyline Visualizer
 */
let map = null;
let hotspotLayerGroup = null;
let routeLayerGroup = null;

function initMap() {
  if (map) return;

  // Center around Chennai / metropolitan study coordinates
  map = L.map('landing-map', {
    center: [13.045, 80.245],
    zoom: 12,
    zoomControl: true
  });

  // Standard OpenStreetMap Tiles (Clean, 100% Free, No Watermark)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  }).addTo(map);

  hotspotLayerGroup = L.layerGroup().addTo(map);
  routeLayerGroup = L.layerGroup().addTo(map);
}

function renderHotspotsOnMap(hotspots) {
  if (!map) initMap();
  hotspotLayerGroup.clearLayers();

  if (!hotspots || hotspots.length === 0) return;

  const bounds = [];

  hotspots.forEach(h => {
    const latLng = [h.latitude, h.longitude];
    bounds.push(latLng);

    const circle = L.circle(latLng, {
      color: h.color,
      fillColor: h.fill_color,
      fillOpacity: 0.45,
      weight: 2,
      radius: h.circle_radius_meters
    });

    const popupContent = `
      <div style="font-family: Inter, sans-serif; min-width: 190px;">
        <h4 style="margin: 0 0 4px 0; color: #0f172a; font-size: 14px; font-weight: 700;">${h.area_name}</h4>
        <div style="display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: ${h.fill_color}; color: ${h.color}; margin-bottom: 8px;">
          ${h.risk_tier} (Rank #${h.rank})
        </div>
        <p style="margin: 2px 0; font-size: 12px; color: #334155;"><b>Recorded Incidents:</b> ${h.incident_count.toLocaleString()}</p>
        <p style="margin: 2px 0; font-size: 12px; color: #334155;"><b>City Share:</b> ${h.percentage_of_total}%</p>
        <p style="margin: 2px 0; font-size: 12px; color: #334155;"><b>Top Crime:</b> ${h.top_crime_type} (${h.top_crime_type_count})</p>
        <p style="margin: 2px 0; font-size: 12px; color: #334155;"><b>Arrest Rate:</b> ${h.arrest_rate_pct}%</p>
      </div>
    `;

    circle.bindPopup(popupContent);
    hotspotLayerGroup.addLayer(circle);

    // Centroid marker dot
    const centerMarker = L.circleMarker(latLng, {
      radius: 4,
      color: '#ffffff',
      fillColor: h.color,
      fillOpacity: 1.0,
      weight: 2
    });
    centerMarker.bindPopup(popupContent);
    hotspotLayerGroup.addLayer(centerMarker);
  });

  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [30, 30] });
  }
}

function renderRoutesOnMap(routes) {
  if (!map) initMap();
  routeLayerGroup.clearLayers();

  if (!routes || routes.length === 0) return;

  const allCoords = [];

  // Draw routes with distinct styles
  routes.forEach((r, idx) => {
    const coords = r.polyline_coordinates;
    coords.forEach(c => allCoords.push(c));

    const isRec = idx === 0;
    const polyline = L.polyline(coords, {
      color: r.color,
      weight: isRec ? 6 : 4,
      opacity: isRec ? 0.95 : 0.65,
      dashArray: isRec ? null : '6, 6'
    });

    const popupHtml = `
      <div style="font-family: Inter, sans-serif;">
        <h4 style="margin:0 0 4px 0; color: ${r.color};">${r.route_id}: ${r.recommendation}</h4>
        <p style="margin:2px 0; font-size:12px;"><b>Risk Score:</b> ${r.risk_score}</p>
        <p style="margin:2px 0; font-size:12px;"><b>Total Distance:</b> ${r.distance_km} km</p>
        <p style="margin:2px 0; font-size:12px;"><b>Crime Exposure:</b> ${r.historical_crime_exposure}</p>
        <p style="margin:2px 0; font-size:12px;"><b>Path:</b> ${r.area_sequence}</p>
      </div>
    `;
    polyline.bindPopup(popupHtml);
    routeLayerGroup.addLayer(polyline);

    // Start & End markers
    if (idx === 0) {
      const startCoord = coords[0];
      const endCoord = coords[coords.length - 1];

      const startIcon = L.divIcon({
        className: 'custom-map-icon',
        html: '<div style="background:#10b981; color:#fff; font-weight:700; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid #fff; box-shadow:0 2px 5px rgba(0,0,0,0.3);">A</div>'
      });
      const endIcon = L.divIcon({
        className: 'custom-map-icon',
        html: '<div style="background:#ef4444; color:#fff; font-weight:700; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid #fff; box-shadow:0 2px 5px rgba(0,0,0,0.3);">B</div>'
      });

      routeLayerGroup.addLayer(L.marker(startCoord, { icon: startIcon }).bindPopup('<b>Starting Point (A)</b>'));
      routeLayerGroup.addLayer(L.marker(endCoord, { icon: endIcon }).bindPopup('<b>Destination Point (B)</b>'));
    }
  });

  if (allCoords.length > 0) {
    map.fitBounds(allCoords, { padding: [40, 40] });
  }
}
