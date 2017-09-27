
/**
 * Give the user the opportunity to change the collection
 * of a photo.
 */
NH.changeCollection = function(key, toId, fromName, toName) {
    html = "<p>The photo is currently in the gallery for " + fromName
        + " but the location you specified is in " + toName
        + ".</p><p>Do you want to move the photo to the gallery for "
        + toName + "?</p>";
    var popup = new NH.Popup(html, {
        title: "Move photo to " + toName + "?",
        buttons: [
            new NH.Button("Move", function(btn) {
                $.post(NH.config.imageSetCollectionUrl,
                       {"image": key, "to": toId,
                        'csrftoken': NH.config.userCsrfToken});
                btn.popup.close();
            }),
            new NH.Button("Don't Move", function(btn) {
                btn.popup.close();
            })
        ]
    })
}

/**
 * Map click callback for the location manager. Generate an
 * ajax request to update the location of an image. If
 * the location lies outside the collection, we offer 
 */
NH.changeLocationClick = function(key, map, editLayer) {
    return function(event) {
        var position = map.getLonLatFromViewPortPx(
            map.events.getMousePosition(event));
        editLayer.removeAllFeatures();
        editLayer.addFeatures([new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(position.lon, position.lat))]);
        $.post(NH.config.imageSetLocationUrl,
               {"image": key, 'x': position.lon, 'y': position.lat,
                'csrftoken': NH.config.userCsrfToken},
               function(resp) {
                   if(resp.changeCollection) {
                       NH.changeCollection(
                           key, resp.to, resp.fromName, resp.toName);
                   }
               });
    }              
}
