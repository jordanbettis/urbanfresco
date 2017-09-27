/**
 * The collection object maintains state for the image list views.
 */
NH.Collection = function(nhLayerName, baseViewPath, initMapCenter) {
    this.nhLayerName = nhLayerName;
    this.baseViewPath = baseViewPath;

    this.featureSelect = function() {
        var t = this;
        return function(feature) {
            t.ajaxLoad(feature.attributes.url, function () {
                NH.map.nhVars.selectCtrl.unselect(feature);
            });
        }
    }

    NH.map = new NH.Map(nhLayerName, initMapCenter);
    NH.map.enableFeatures(this.featureSelect());
    NH.map.enableNavigation();
    this.updateMapLocation = function() {
        var t = this;
        return function(event) {
            NH.updateBrowserState();
        }
    }
    
    NH.map.events.on({"moveend": this.updateMapLocation()});        
    
    /**
     * Load a collection. This function assumes the html is already
     * in place. To fetch a collection via ajax and load it, use
     * ajaxLoad.
     */
    this.load = function(collectionPath, ajaxParams) {
        var t = this;
        this.collectionPath = collectionPath;
        this.ajaxParams = ajaxParams;

        $("#slider").hide();

        $("#content-column .close").off("click");
        $("#content-column .close").on("click", function() {
            $("#content-container").children().remove();
            NH.updateBrowserState(t.baseViewPath);
            if(t.ssWidget) t.unloadSlideShow()();
            t.ajaxLoad(t.baseViewPath);
        });

        $("#content-column .minimize").off("click");
        $("#content-column .minimize").on("click", function() {
            t.scrollPosition = $(window).scrollTop();
            NH.zoomTransition($("#content-column"), $("#content-minimized"));
        });
        $("#content-minimized").off("click");
        $("#content-minimized").live("click", function() {
            NH.zoomTransition(
                $("#content-minimized"), $("#content-column"),
                function() {
                    $(window).scrollTop(t.scrollPosition);
                });
        });

        this.initImageClick();

        if(NH.config.userAuthenticated) {
            NH.initUpload($("#content-column"), $("#upload-form"),
                function(event, data) {
                    var prependTo = $("#content-column ol.thumbnails");
                    for(var i = 0; i < data.result.length; i++) {
                        var file = data.result[i];
                        prependTo.prepend(
                            '<li><a href="' + file['show_url'] + '"> ' +
                                '<img src="' + file['thumbnail_url'] +
                                '" alt="loading.."></a></li>');
                    }
                    var request = $(".request");
                    if(request)
                        request.remove();
                    t.initImageClick()
                });
        }
    }

    /**
     * Activate the click event on gallery images
     */
    this.initImageClick = function() {
        var t = this;
        $("ol.thumbnails a").off("click");
        $("ol.thumbnails a").on("click", function(event) {
            var imageKey = $(event.currentTarget).attr("href").match(/\d+/)[0];
            t.loadSlideshow(imageKey);
            return false;
        });
    }

    /**
     * If the user is looking at their userroot, we want to activate the
     * ajax controls
     */
    this.initUserControls = function() {
        var t = this;        
        this.profileEdit = new NH.AjaxForm(
            $(".edit-profile"), function(response) {
                if(response['profile'] != null)
                    $(".up-profile").html(response['profile']);
            });
        this.nameEdit = new NH.AjaxForm(
            $(".edit-name"), function(response) {
                if(response['name'] != null)
                    $(".up-name").html(response['name']);
            });
        
        NH.initUpload($(".up-avatar"), $("#avatar-upload-form"),
                   function(event, data) {
                       $(".up-avatar img").attr("src", data.result[0].url);
                   });
    }

    /**
     * Load a collection given by 'url' via ajax
     */
    this.ajaxLoad = function(url, callback) {
        var t = this;
        $.get(url, function(resp) {
            $("#content-container").html(resp['html']);
            var params = {"collection_id": resp['collectionId'],
                          "user_name": resp['userName']}

            if(resp['collectionId'] !== undefined) {
                t.load(resp['collectionPath'], params);
            } else if(resp['sliderInitImage'] !== undefined && 
                      $(window).height() > 500) {
                t.unloadSlider();
                t.loadSlider(resp['sliderInitImage'], params);
            }
            
            if(resp['imageKey'] !== undefined)
                t.loadSlideshow(resp['imageKey']);
            else {
                if($('#slide-show').is(':visible'))
                    $(".ss-close").click();
                // Only call this if we're not loading the slideshow
                // since the slideshow calls this in endSlide.
                NH.updateBrowserState(url);
            }

            if(resp['showUserControls'])
                t.initUserControls();

            if(callback != undefined)
                callback();

        });
    }

    /* Launch the image slider widget on the bottom of the page */
    this.loadSlider = function(imageKey, ajaxParams) {
        var t = this;
        $("#slider").show();

        var initSliderClick = function(image) {
            $("#slider-viewport div div img").on('click', function(event) {
                var imageKey = $(event.currentTarget).attr("src").match(/\d+/)[0];
                for(var i = 0; i < t.sliderWidget.images.length; i++) {
                    var image = t.sliderWidget.images[i];
                    if(image['key']==imageKey) {
                        t.ajaxLoad(image['collection_url'], function() {
                            t.loadSlideshow(imageKey);
                        });
                        break;
                    }
                }
            });
        }
        
        this.sliderWidget = new NH.SlideWidget(
            $("#slider-viewport"), imageKey, true, ajaxParams, initSliderClick);

        $(".slider-next").on("click", function(event) {
            t.sliderWidget.goNext(initSliderClick);
        });
        $(".slider-previous").on("click", function(event) {
            t.sliderWidget.goPrevious(initSliderClick);
        });

    }

    /* Hide and undo state on the slider at the bottom of the page */ 
    this.unloadSlider = function() {
        $("#slider").hide();
        $("#slider-viewport").html("");
        $("#slider").find("*").off();
    }

    /**
     * Launch the slideshow with imageKey. Will create a this.ssWidget object
     * containing the widget.
     */
    this.loadSlideshow = function(imageKey) {
        var t = this;

        if(this.ssWidget != null)
            this.unloadSlideShow()();

        $("#ss-viewport").html("");
        
        $("#site-header").slideUp("medium");
        $("#slide-show").show();
        $("#content-column .minimize").click();

        this.locationMarkLayer = NH.map.enableLocationMark();

        this.votes = Object();
        
        this.ssWidget = new NH.SlideWidget(
            $("#ss-viewport"), imageKey, false,
            this.ajaxParams, this.ssEndSlide());

        $(window).off("resize");
        $(window).on("resize", function() {
            t.ssWidget.configureSize()
        });
        
        if(Modernizr.touch) {
            $("ss-slide-control").hide();
            
        } else {
            $(".ss-next").on("click", function(event) {
                t.ssWidget.goNext(t.ssEndSlide());
            });
            $(".ss-previous").on("click", function(event) {
                t.ssWidget.goPrevious(t.ssEndSlide());
            });
        }

        if(Modernizr.touch) {
            $("slide-show").on("touch", this.ssStartHideControls());
        } else {
            $("#ss-viewport").on("mousemove", this.ssStartHideControls());
            $(".ss-widget-bar").on("mouseenter", this.ssStopHideControls());
            $(".ss-widget-bar").on("mouseleave", this.ssStartHideControls());
            $(".ss-slide-control").on("mouseenter", this.ssStopHideControls());
        }

        $(".ss-close").on("click", this.unloadSlideShow());
        $(".ss-minimize").on("click", function() {
            $("#site-header").slideDown("medium");
            NH.zoomTransition($("#slide-show"), $("#ss-minimized"));
        });
        $(".ss-nh-name").on("click", this.unloadSlideShow());
        
        $("#ss-minimized").off("click");
        $("#ss-minimized").on("click", function() {
            $("#site-header").slideUp("medium");
            NH.zoomTransition($("#ss-minimized"), $("#slide-show"));
        });

    }
    
    /* Set or reset a timeout to hide the slide show controls */
    this.ssStartHideControls = function() {
        var t = this;
        return function () {
            t.ssStopHideControls();
            //t.timeoutID = setTimeout(function () {
            //    $(".ss-widget-bar").fadeOut("fast");
            //    $(".ss-slide-control").fadeOut("fast");
            //}, 4000);
        }
    }

    /* Show the controls and/or cancel the timeout */
    this.ssStopHideControls = function() {
        var t = this;
        return function () {
            clearTimeout(t.timeoutID);
            $(".ss-widget-bar").fadeIn("fast");
            if(!Modernizr.touch)
                $(".ss-slide-control").fadeIn("fast");
        }
    }

    /**
     * A callback for when the user clicks on the upvote button
     */
    this.ssUpvoteImage = function () {
        var t = this;
        return function(event) {
            $(".ss-upvote-widget").off("click");
            $(".ss-upvote-widget").removeClass("ss-upvote");
            $(".ss-upvote-widget").addClass("ss-upvoted");
            
            var image = t.ssWidget.images[t.ssWidget.currentIndex];

            image['votes'] += 1;
            t.votes[image['key']] = true;
            $(".ss-votes").children(".value").html(image['votes']);
            t.ssSendVotes()();
        }
    }

    /**
     * Returns a function which sends any queued up vote information
     * to the server.
     */
    this.ssSendVotes = function() {
        var t = this;
        return function() {
            var postData = $.extend({}, t.votes, {
                csrftoken: NH.config.userCsrfToken});
            $.post(NH.config.imageVoteUrl, postData, function (event) {
                t.votes = Object();
            });
        }
    }
    
    /**
     * The callback that gets called whenever the slideshow
     * is slid or created.
     */
    this.ssEndSlide = function() {
        var t = this;
        return function(image) {
            $("#ss-bottom-bar").find("*").off();
            t.locationMarkLayer.removeAllFeatures();
            $(".image-description").html("");

            if(image == null){
                t.unloadSlideShow()();
            } else {
                if(t.votes[image['key']] === undefined)
                    t.votes[image['key']] = false;
                if(image['editable']) {
                    $(".ss-utils").show();
                    $(".ss-utils").attr("href", image['utils_url']);
                    var imageManager = new NH.ImageManager(image['key'], {
                        descriptionDone: function(result) {
                            image['description'] = result['description'];
                            $(".image-description").html(result['description']);
                        },
                        deleteDone: function(result) {
                            image['img-element'].attr(
                                "src", "/static/img/notavail-view.jpg");
                        }
                    });
                    imageManager.makePopupClick($(".ss-utils"));
                    if(!image['description']) {
                        var descEdit = $('<a>[add description]</a>').appendTo(
                            $(".image-description"));
                        descEdit.attr("href", NH.config.imageDescription +
                                      "?key=" + image["key"]);
                        var descForm = new NH.AjaxForm(descEdit, function(result){
                            image['description'] = result['description'];
                            $(".image-description").html(result['description']);
                        });
                    }
                            
                } else {
                    $(".ss-utils").hide();
                }

                if(image['way']) {
                    $(".ss-where").hide();
                    $(".ss-location").show();
                    $(".ss-location").on("click", function(event) {
                        $("#site-header").slideDown("medium");
                        NH.zoomTransition(
                            $("#slide-show"), $("#ss-minimized"));
                        NH.map.panTo(new OpenLayers.LonLat(
                            image.way[0], image.way[1]));
                    });
                    t.locationMarkLayer.addFeatures([new OpenLayers.Feature.Vector(
                        new OpenLayers.Geometry.Point(image.way[0], image.way[1]))]);
                }
                else if(image['editable']) {
                    $(".ss-location").hide();
                    $(".ss-where").show();
                    $(".ss-where").attr("href", image['location_url']);
                } else {
                    $(".ss-location").hide();
                    $(".ss-where").hide(); 
                }
                
                if(image['votable'] && !t.votes[image['key']]) {
                    $(".ss-upvote-widget").removeClass("ss-upvoted");
                    $(".ss-upvote-widget").addClass("ss-upvote");
                    $(".ss-upvote-widget").on("click", t.ssUpvoteImage());
                } else {
                    $(".ss-upvote-widget").removeClass("ss-upvote");
                    $(".ss-upvote-widget").addClass("ss-upvoted");
                }

                if(image['description'])
                    $(".image-description").html(image['description']);
                $(".ss-votes").children(".value").html(image['votes']);
                $(".ss-views").children(".value").html(
                    Number(image['views']) + 1);
                $(".ss-user-icon img").attr("src", image['user_tiny_avatar']);
                $(".ss-user .name").html(image['user_display_name']);
                $(".ss-user .name").attr("href", image['user_url']);
                $(".ss-nh-name").html(image['collection_name']);
                $(".ss-nh-name").attr("href", image['collection_url']);
                $(".ss-user .map-link").attr("href", image['user_url']);
                $("#ss-minimized img").attr("src", image['thumb']);
                if(image['ratio'] > 1.3333) {
                    $("#ss-minimized img").css({
                        "width": "80px",
                        "height": 80 / image['ratio'] + "px"});
                } else {
                    $("#ss-minimized img").css({
                        "width": 60 * image['ratio'] + "px",
                        "height": "60px"});
                }
                NH.updateBrowserState(image['url']);
                t.ssStartHideControls()();
            }
        }
    }

        


    /* Hide and undo state on the slideshow */ 
    this.unloadSlideShow = function() {
        var t = this;
        return function(event) {
            $("#slide-show").find("*").off();
            $("#slide-show").hide();
            $("#site-header").slideDown("medium");
            $("#content-minimized").click();
            $("#ss-viewport").html("");
            $("#ss-minimized").hide();
            var postData = $.extend({}, t.votes, {
                csrftoken: NH.config.userCsrfToken});
            $.post(NH.config.imageVoteUrl, postData, function (event) {
                t.votes = Object();
            });
            t.ssWidget = null;
            NH.updateBrowserState(t.collectionPath);
            if(t.locationMarkLayer) {
                NH.map.removeLayer(t.locationMarkLayer);
                t.locationMarkLayer = null;
            }
            return false;
        }
    }
}


/**
 * These functions manage the pushState functionaliy.
 */
NH.updateBrowserState = function(url) {
    var currentURL = window.location.pathname;
    var currentQS = window.location.search;

    if(url && url == currentURL)
        return;

    center = NH.map.getCenter();
    data = {
        url: url,
        x: center.lon,
        y: center.lat,
        z: NH.map.zoom
    };

    var newQS = "?l=" + data.x + "," + data.y + "," + data.z;

    if(url != null || newQS != currentQS) {
        if(url == null) {
            window.history.replaceState(data, "", currentURL + newQS);
        } else {
            window.history.pushState(data, "", url + newQS);
        }
    }
}

window.onpopstate = function(event) {
    var collection = $("#content-container").data("collection");
    
    if(event.state.x && event.state.y && event.state.z) {
        NH.map.moveTo(new OpenLayers.LonLat(
            event.state.x, event.state.y), event.state.z);
    }
    if(event.state.url != "") {
        NH.collection.ajaxLoad(event.state.url);
    }
}    
