"use strict";
const $ = (id) => document.getElementById(id);
const state = {pickup: null, dropoff: null, pickupMarker: null, dropoffMarker: null};
const map = L.map("map").setView([40.744, -73.985], 12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);
function markerIcon(letter, classname) {
  return L.divIcon({className:"", html:`<div class="taxi-marker ${classname}">${letter}</div>`, iconSize:[30,30], iconAnchor:[15,15]});
}
function showStatus(message, isError=false) {
  $("status").textContent = message;
  $("status").classList.toggle("error", isError);
}
function coordText(point) {return point ? `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}` : "Kliknij punkt na mapie";}
function refresh() {
  $("pickupText").textContent = state.pickup ? coordText(state.pickup) : "Kliknij pierwszy punkt na mapie";
  $("dropoffText").textContent = state.dropoff ? coordText(state.dropoff) : "Kliknij drugi punkt na mapie";
  $("predictBtn").disabled = !(state.pickup && state.dropoff);
  if (state.pickupMarker) map.removeLayer(state.pickupMarker);
  if (state.dropoffMarker) map.removeLayer(state.dropoffMarker);
  state.pickupMarker = state.pickup ? L.marker(state.pickup, {icon:markerIcon("A","a")}).addTo(map) : null;
  state.dropoffMarker = state.dropoff ? L.marker(state.dropoff, {icon:markerIcon("B","b")}).addTo(map) : null;
  $("result").hidden = true;
  showStatus(state.pickup && state.dropoff ? "Gotowe — kliknij «Oblicz czas przejazdu»." : "Zaznacz dwa punkty na mapie.");
}
map.on("click", (event) => {
  const point = {lat:event.latlng.lat, lng:event.latlng.lng};
  if (!state.pickup || (state.pickup && state.dropoff)) {state.pickup=point;state.dropoff=null;}
  else {state.dropoff=point;}
  refresh();
});
$("swapBtn").addEventListener("click", () => {
  if (!state.pickup || !state.dropoff) return;
  [state.pickup,state.dropoff]=[state.dropoff,state.pickup];refresh();
});
$("clearBtn").addEventListener("click", () => {state.pickup=null;state.dropoff=null;refresh();});
$("predictForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.pickup || !state.dropoff) return;
  const hour = Number.parseInt($("hour").value.split(":")[0], 10);
  if (!Number.isInteger(hour) || hour < 0 || hour > 23) {showStatus("Wybierz poprawną godzinę.", true);return;}
  const payload = {
    pickup:{latitude:state.pickup.lat,longitude:state.pickup.lng},
    dropoff:{latitude:state.dropoff.lat,longitude:state.dropoff.lng},
    weekday_1_7:Number($("weekday").value), hour_0_23:hour,
  };
  $("predictBtn").disabled=true;
  showStatus("Obliczam trasę i predykcję...");
  $("result").hidden = true;
  try {
    const response=await fetch("/predict", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const data=await response.json();
    if (!response.ok) {
      const detail=typeof data.detail==="string" ? data.detail : "Sprawdź wybrane punkty i spróbuj ponownie.";
      throw new Error(detail);
    }
    $("minutes").textContent=data.predicted_travel_time_min.toFixed(2);
    $("distance").textContent=`${(data.routing_distance_m/1000).toFixed(2)} km`;
    $("zoneIds").textContent=`${data.pickup_location_id} / ${data.dropoff_location_id}`;
    $("streets").textContent=data.route_street_names.length ? data.route_street_names.join(", ") : "Brak danych o ulicach.";
    $("result").hidden=false;
    showStatus("Predykcja obliczona pomyślnie.");
  } catch (error) {showStatus(`Nie udało się obliczyć predykcji: ${error.message}`, true);}
  finally {$("predictBtn").disabled=!(state.pickup && state.dropoff);}
});
refresh();
