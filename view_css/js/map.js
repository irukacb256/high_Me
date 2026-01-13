window.mapInstance = null;
window.initMap = function() {
    const mapElement = document.getElementById("google-map");
    if (!mapElement) return;
    const mapOptions = {
        zoom: 14,
        center: mapCenterData,
        disableDefaultUI: true,
        zoomControl: true,
        styles: [{ featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }]
    };
    window.mapInstance = new google.maps.Map(mapElement, mapOptions);
    mapPinsData.forEach(pin => {
        new google.maps.Marker({
            position: { lat: pin.lat, lng: pin.lng },
            map: window.mapInstance,
            title: pin.title,
        });
    });
};