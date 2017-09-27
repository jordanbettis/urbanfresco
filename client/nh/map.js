
NH.Map = OpenLayers.Class(OpenLayers.Map, {
    /**
     * This creates the map initialized using our config. nhLayerName
     * is the tms name for the base layer ('nh' or a user's
     * name). Center is optional.
     *
     * This doesn't create the navigation controls. You must run
     * enableNavigation to create them, but if you want hover actions,
     * enableHover must be called first.
     */
    initialize: function(nhLayerName, center) {
        var nhLayer = new OpenLayers.Layer.TMS(
            nhLayerName, NH.config.mapserverUrl, {
                layername: nhLayerName,
                type:'png',
                serviceVersion: '',
                isBaseLayer: false});

        OpenLayers.Map.prototype.initialize.apply(this, ["map", {
            maxExtent: new OpenLayers.Bounds(
                NH.config.bounds.minx, NH.config.bounds.miny,
                NH.config.bounds.maxx, NH.config.bounds.maxy),
            resolutions: NH.config.resolutions,
            numZoomLevels: NH.config.numZoomLevels,
            maxResolution: "auto",
            units: 'm',
            controls: [],
            size: new OpenLayers.Size(NH.config.tile_size, NH.config.tile_size),
            projection: new OpenLayers.Projection(NH.config.srsName)}]);
        
        this.addLayer(nhLayer);
        this.setBaseLayer(nhLayer);

        // An array of variables useful for nh code.
        this.nhVars = {
            "nhLayerName": nhLayerName,
            "nhLayer": nhLayer,
        }   
        
        if (center == null)
            this.setCenter(new OpenLayers.LonLat(
                NH.config.centerX, NH.config.centerY), NH.config.centerZ);
        else
            this.setCenter(new OpenLayers.LonLat(
                center.x, center.y), center.z);

    },

    /**
     * Create an OpenLayers.Rule object to control the
     * visual display of vector objects at given scales.
     */
    makeRule: function(type, min, max, symbolizer) {
            var params = {
                filter: new OpenLayers.Filter.Comparison({
                    type: OpenLayers.Filter.Comparison.EQUAL_TO,
                    property: "type",
                    value: type}),
                symbolizer: symbolizer}

            var gs = OpenLayers.Util.getScaleFromResolution;
            if(min) params['minScaleDenominator'] = gs(min, "m");
            if(max) params['maxScaleDenominator'] = gs(max, "m");
            
            return new OpenLayers.Rule(params);
    },

    /**
     * Create the vector-based features, including hover events and
     * popups.
     *
     * Due to conflicts with TouchNavigation, this must be called
     * before enableNavigation.
     */
    enableFeatures: function(selectCallback) {

        var rules = [
            this.makeRule("image", null, 8, {
                graphicZIndex: 100, pointRadius: 6, fillOpacity: 1}),
            this.makeRule("image", 8, 32, {
                graphicZIndex: 100, pointRadius: 5, fillOpacity: 1}),
            this.makeRule("image", 32, null, {
                graphicZIndex: 100, pointRadius: 3, fillOpacity: 1}),
            this.makeRule("collection", null, null, {graphicZIndex: 1})
        ];
        
        var defaultStyle = new OpenLayers.Style({
            fillOpacity: 0,
            strokeColor: "#ff3d00",
            externalGraphic: "/static/img/marker.png",
            strokeWidth: 2
        });

        defaultStyle.addRules(rules);
        
        var selectStyle = new OpenLayers.Style({
            strokeColor: "#ffbc11",
            fillColor: "#ffbc11",
            externalGraphic: "/static/img/marker-high.png",
            strokeWidth: 2
        });

        var hoverRules = [
            this.makeRule("collection", null, 16, {
                graphicZIndex: 100, fillOpacity: .04}),
            this.makeRule("collection", 16, 32, {
                graphicZIndex: 100, fillOpacity: .20}),
            this.makeRule("collection", 32, null, {
                graphicZIndex: 100, fillOpacity: .40})];

        selectStyle.addRules(hoverRules.concat(rules));

        var styleMap = new OpenLayers.StyleMap({
            "default": defaultStyle,
            "select": selectStyle});
                        
        var featuresLayer = new OpenLayers.Layer.Vector("features", {
            rendererOptions: {zIndexing: true},
            strategies: [new OpenLayers.Strategy.BBOX()],
            protocol: new OpenLayers.Protocol.HTTP({
                url: "/photos/features.json",
                params: {"layer": this.nhVars.nhLayerName},
                format: new OpenLayers.Format.GeoJSON(),
            }),
            styleMap: styleMap
        });

        this.addLayer(featuresLayer);
        
        var highlightCtrl = new OpenLayers.Control.SelectFeature(featuresLayer, {
            hover: true,
            highlightOnly: true,
        });

        t = this;
        highlightCtrl.events.on({
            "featurehighlighted": function(event) {
                var fea = event.feature;

                if(fea.nhTimeoutID) clearTimeout(fea.nhTimeoutID);
                if(fea.nhPopup) return;
                
                if(fea.attributes.type == "image") {
                    var popup = new OpenLayers.Popup.FramedCloud(
                        "imagePopup", OpenLayers.LonLat.fromString(
                            fea.geometry.toShortString()),
                        new OpenLayers.Size(150,150),
                        "<img src=" + fea.attributes.thumb + ">",
                        {size: new OpenLayers.Size(0, 10),
                         offset: new OpenLayers.Pixel(-1, -4)}, false);
                    fea.nhPopup = popup;
                    t.addPopup(popup);
                }
            },
            "featureunhighlighted": function(event) {
                var fea = event.feature;

                if(fea.timeoutID) clearTimeout(fea.nhTimeoutID);

                if(fea.attributes.type == "image") {
                    fea.nhTimeoutID = setTimeout(function () {
                        if(fea.nhPopup) {
                            t.removePopup(fea.nhPopup);
                            fea.nhPopup.destroy();
                            fea.nhPopup = null;
                        }
                    }, 500);
                }
            }
        });

        this.addControl(highlightCtrl);
        highlightCtrl.activate();
        this.nhVars.highlightCtrl = highlightCtrl;
            
        var selectCtrl = new OpenLayers.Control.SelectFeature(featuresLayer, {
            hover: false,
            onSelect: selectCallback
        });
        this.addControl(selectCtrl);
        selectCtrl.activate();
        this.nhVars.selectCtrl = selectCtrl;

    },


    /**
     * Create the keyboard and touch navigation controls.
     */
    enableNavigation: function(clickCallback) {
        this.addControl(new OpenLayers.Control.KeyboardDefaults());
        
        this.addControl(new OpenLayers.Control.TouchNavigation({
            dragPanOptions: {enableKinetic: true},
            defaultClick: clickCallback,
        }));
        
        navPos = function(event) {
            var x = event.pageX - event.target.offsetLeft;
            var y = event.pageY - event.target.offsetTop;
            
            if(y < 25)
                position = "up";
            else if (y <= 50) {
                if (x <= 40)
                    position = "left";
                else
                    position = "right";
            }
            else if (y <= 80)
                position = "down";
            else 
                position = "none";
            return position;
        }

        // If this isn't a touch device, activate and show nav controls
        if(!Modernizr.touch) {
            $("#nav").show();
            $("#zoom-controls").show();
            $("#nav").bind("mousemove", function(event) {
                mousePos = navPos(event);
                switch(mousePos) {
                case "up":
                    $(event.currentTarget).css(
                        {"background-position": "-80px 0px"});
                    break;
                case "down":
                    $(event.currentTarget).css(
                        {"background-position": "-160px 0px"});
                    break;
                case "left":
                    $(event.currentTarget).css(
                        {"background-position": "-240px 0px"});
                    break;
                case "right":
                    $(event.currentTarget).css(
                        {"background-position": "-320px 0px"});
                    break;
                }
            });
            
            $("#nav").bind("mouseleave", function(event) {
                $(event.currentTarget).css({"background-position": "0px 0px"});
            });

            var t = this;
            $("#nav").bind("click", function(event) {
                var xSlideFactor = $(window).innerWidth() / 2;
                var ySlideFactor = $(window).innerHeight() / 2;
                var buttonPress = null;
                
                buttonPress = navPos(event)
                
                switch(buttonPress) {
                case "up":
                    t.pan(0, -ySlideFactor);
                    break;
                case "down":
                    t.pan(0, ySlideFactor);
                    break;
                case "left":
                    t.pan(-xSlideFactor, 0);
                    break;
                case "right":
                    t.pan(xSlideFactor, 0);
                    break;
                }
                
            });
            
            $(".zoom-in").bind("click", function() {
                t.zoomIn();
            });
            $(".zoom-out").bind("click", function() {
                t.zoomOut();
            });
        }
        
    },

    /**
     * Configure the map for editing the location of an image
     */
    enableImageLocation: function() { 
        var style = new OpenLayers.Style({
                fillOpacity: 1,
                strokeColor: "#ff3d00",
                externalGraphic: "/static/img/marker.png",
                strokeWidth: 2,
                pointRadius: 6
        });

        var layer = new OpenLayers.Layer.Vector("edit", {
            "styleMap": new OpenLayers.StyleMap({"default": style})
        });
        this.addLayer(layer);
        return layer;
    },

    /**
     * Create a layer upon which we can draw a circle around the
     * location of the current photo.
     */
    enableLocationMark: function() {
        var style = new OpenLayers.Style({
            fillOpacity: 0,
            strokeColor: "#ffbc11",
            strokeWidth: 2,
            pointRadius: 20
        });

        var layer = new OpenLayers.Layer.Vector("mark", {
            "styleMap": new OpenLayers.StyleMap({"default": style})
        });
        this.addLayer(layer)
        return layer;
    }
});
