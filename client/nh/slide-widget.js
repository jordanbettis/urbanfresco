/**
 * viewport: jquery element
 * initialImages: json list of imageData
 * viewIndex: index (of the json) of the image that will initially
 *   be in the viewport (if showMultiple, it will be the leftmost
 *   visible object
 * showMultiple: boolean, should multiple images be visible in the
 *   viewport at once?
 * ajaxParams: the parameters to the ajaxrequest for more images
 */
NH.SlideWidget = function(
    viewport, imageKey, showMultiple, ajaxParams, doneCallback) {
    
    this.viewport = viewport;
    this.showMultiple = showMultiple;
    this.images = [];
    this.currentIndex = 0;
    this.ajaxParams = ajaxParams;
    this.slider = $("<div>").appendTo(this.viewport);
    this.doneCallback = doneCallback;
    this.sliderWidth = 0;

    if(this.showMultiple)
        this.countViews = false;
    else
        this.countViews = true;
        

    this.configureSize = function () {
        var t = this;
        this.containerHeight = viewport.height();
        if(!this.showMultiple)
            this.containerWidth = viewport.width();
        
        // Find the image size that most closely fits the viewport
        this.size = "max";
        var heightDiff = 5000;
        $.each(NH.config.imageSizes, function(index, size) {
            var diff = Math.abs(size.height - t.containerHeight);
            if(diff <= heightDiff && size.height >= t.containerHeight) {
                heightDiff = diff;
                t.size = size.name;
            }
        });

        $.each(this.images, function(index, item) {
            t.sizeElement(item);
        });
        
        if(this.showMultiple)
            $.each(this.images, function(index, value) {
                t.sliderWidth += Math.ciel(t.containerHeight * value['ratio']);
            });
        else 
            this.sliderWidth = this.containerWidth * this.images.length;
        
        this.slider.css(
            {"position": "relative",
             "height": "100%",
             "width": this.sliderWidth + "px",
             "left": this.currentLeft() + "px"});

        this.slider.on("swipeleft", function() { 
            t.goNext(t.doneCallback);
        });
        this.slider.on("swiperight", function() { 
            t.goPrevious(t.doneCallback);
        });
    }

    this.currentLeft = function() {
        var shift = 0;
        var t = this;
        if(this.showMultiple) {
            $.each(this.images, function(index, value) {
                if(index == t.currentIndex)
                    return false;
                else
                    shift += t.containerHeight * value['ratio'];
            });
        } else {
            shift = this.containerWidth * this.currentIndex;
        }
        return -shift;
    }

    this.sizeElement = function(item) {
        var containerHeight = this.containerHeight;
        if(this.showMultiple) {
            var containerWidth = item['ratio'] * containerHeight;
            var containerRatio = item['ratio'];
            var imgWidth = containerWidth - 2;
            var imgHeight = containerHeight - 2;
        } else {
            var containerWidth = this.containerWidth;
            var containerRatio = this.containerWidth / containerHeight;
            var imgWidth = this.containerWidth;
            var imgHeight = this.containerHeight;
        }
        
        item['div-element'].css({"width": containerWidth + "px",
                                 "height": containerHeight + "px",
                                 "float": "left",
                                 "overflow": "hidden"});
        
        if(item['ratio'] < containerRatio) {
            width = imgHeight * item['ratio'];
            item['img-element'].css({
                "position": "relative",
                "width": width + "px",
                "height": imgHeight + "px",
                "left": ((containerWidth - width) / 2) + "px",
                "top": ((containerHeight - imgHeight) / 2) + "px"
            });
        } else {
            height = imgWidth / item['ratio'];
            item['img-element'].css({
                "position": "relative",
                "width": imgWidth + "px",
                "height": height + "px",
                "left": ((containerWidth - imgWidth) / 2) + "px",
                "top": ((containerHeight - height) / 2) + "px"
            });
        }
    }
    
    this.makeElement = function(item, append) {
        if(append) {
            this.images.push(item);
            var element = $(
                '<div><img src="' + item[this.size] + '"></div>').appendTo(
                    this.slider);
        } else {
            this.images.unshift(item);
            var element = $(
                '<div><img src="' + item[this.size] + '"></div>').prependTo(
                    this.slider);
            this.currentIndex++;
        }
        item['div-element'] = element;
        item['img-element'] = element.children();

        this.sizeElement(item);
        if(this.showMultiple) {
            this.sliderWidth += Math.ceil(item['ratio'] * this.containerHeight);
        } else {
            this.sliderWidth = this.containerWidth * this.images.length;
        }

        this.slider.css({
            "width": this.sliderWidth + "px",
            "left": this.currentLeft() + "px"
        });
    }

    /**
     * Fetch a new images via ajax. Next is a boolean indicating if
     * we should use the next or previous.
     *
     * The function will fetch as many images as there are keys in
     * the list, and attempt to replace the keys with the same number
     */
    this.fetchElement = function(next, callback) {
        if(next) {
            var keys = this.nextFetch.join();
            var getData = $.extend(
                {}, this.ajaxParams, {
                    "keys": keys, "next": true, "count": this.countViews});
        } else {
            var keys = this.previousFetch.join();
            var getData = $.extend(
                {}, this.ajaxParams, {
                    "keys": keys, "previous": true, "count": this.countViews});
        }

        if(keys == "") {
            if(callback instanceof Function)
                callback(this.images[this.currentIndex]);
            return;
        }

        var t = this;
        $.get(NH.config.imageGetUrl, getData, function(data) {
            $.each(data, function(i, item) {
                t.makeElement(item, next);
            });
            if(next) {
                t.nextFetch = data[data.length - 1]['next'].slice(
                    0, t.nextFetch.length);
            } else {
                t.previousFetch = data[0]['previous'].slice(
                    0, t.previousFetch.length);
            }
            if(callback instanceof Function)
                callback(t.images[t.currentIndex]);
        });
    }
    
    /**
     * Slide to or fro. 
     */
    this.slide = function(callback) {
        var t = this;
        this.slider.animate(
            {"left": this.currentLeft()}, "medium",
            function () {
                if(callback instanceof Function)
                    callback(t.images[t.currentIndex]);
            });
    }

    /**
     * Return how many images to move forward or back to scroll off
     * all images currently in the viewport
     */
    this.viewportMoveCount = function(forward) {
        if(!this.showMultiple)
            return 1;
        
        var moveCount = 0;
        if(forward)
            var i = this.currentIndex;
        else
            var i = this.currentIndex - 1;
        var processedWidth = 0;
        while(i >= 0 && i < this.images.length) {
            var itemWidth = this.images[i]['ratio'] * 
                this.containerHeight;
            if(processedWidth + itemWidth > this.viewport.width()) {
                return moveCount;
            } else {
                moveCount++;
                if(forward)
                    i++
                else
                    i--;
                processedWidth += itemWidth
            }
        }
        return moveCount;
    }
    
    this.goNext = function(callback) {
        var moveCount = this.viewportMoveCount(true);
        if(this.images.length - this.currentIndex < (moveCount + 1) * 2)
            this.fetchElement(true);
        
        if(this.currentIndex < this.images.length - moveCount) {
            this.currentIndex += moveCount;
            this.slide(callback);
        } else {
            if(callback instanceof Function)
                callback(null);
        }
    }

    this.goPrevious = function(callback) {
        var moveCount = this.viewportMoveCount(false);
        var t = this;
        var callBack = function(item) {
            if(callback instanceof Function)
                callback(item);
            if(t.currentIndex < (moveCount + 1) * 2)
                t.fetchElement(false);
        }
        
        if(this.currentIndex - moveCount >= 0) {
            this.currentIndex -= moveCount;
            this.slide(callBack);
        } else {
            if(callback instanceof Function)
                callback(null);
        }
        
    }

    this.init = function() {
        var t = this;
        var getData = $.extend(
            {}, this.ajaxParams,
            {"keys": imageKey, "previous": true, "next": true,
             "count": this.countViews});

        $.get(NH.config.imageGetUrl, getData, function(data) {
            t.configureSize();
            t.makeElement(data[0], true);
            // The previous/next image to fetch via ajax
            if(t.showMultiple) {
                t.previousFetch = data[0]['previous']
                t.nextFetch = data[0]['next']
            } else {
                t.previousFetch = data[0]['previous'].slice(0, 1);
                t.nextFetch = data[0]['next'].slice(0, 2);
            }
            t.fetchElement(true, function() {
                t.fetchElement(false, t.doneCallback);
            });
        });
    }
    this.init()
}
