
{% import "macros.html" as macros %}

{# WARNING WARNING WARNING WARNING #}
{# DO NOT PULL ANY SENSITIVE VARIABLES INTO THE JAVASCRIPT #}

function nhConfig() {
    this.tileSize = {{ config.MAP['tile-size'] }};
    this.bounds = {minx: {{ config.MAP['min'][0] }},
                   miny: {{ config.MAP['min'][1] }},
                   maxx: {{ config.MAP['max'][0] }},
                   maxy: {{ config.MAP['max'][1] }} };
    this.resolutions = {{ config.MAP['zoom'] }};
    this.numZoomLevels = this.resolutions.length;
    this.srsName = "{{ config.MAP['srs-name'] }}";
    this.origin = [{{ config.MAP['origin'][0] }}, {{ config.MAP['origin'][1] }}];
    this.mapserverUrl = "{{ config.MAPSERVER_URL }}";
    this.maxUploadSize = {{ config.MAX_UPLOAD_SIZE }};

    this.imageGetUrl = "{{ request.url_for('images-get') }}";
    this.imageDeleteUrl = "{{ request.url_for('images-delete') }}";
    this.imageVoteUrl = "{{ request.url_for('images-vote') }}";
    this.imageSetLocationUrl = "{{ request.url_for('images-set-location') }}";
    this.imageSetCollectionUrl = "{{ request.url_for('images-set-collection') }}";
    this.imageDescription = "{{ request.url_for('images-description') }}";
    this.imageManageUrl = "{{ request.url_for('staticpage-manage-image') }}";

    this.centerX = {{ config.MAP['default-center']['x'] }};
    this.centerY = {{ config.MAP['default-center']['y'] }};
    this.centerZ = {{ config.MAP['default-center']['z'] }};

    this.imageSizes = [
        {%- for size in config.IMAGE_SIZES %}
          {width: {{ size[0] }},
           height: {{ size[1] }},
           name: "{{ size[2] }}"}{% if not loop.last %},{% endif %}
        {%- endfor -%}];

    this.notAvailable = {
        {%- for size in config.IMAGE_SIZES %}
          {{ size[2] }}: "{{ config.STATIC_URL }}/img/notavail-{{ size[2] }}.jpg"
          {%- if not loop.last -%},{%- endif %}
        {%- endfor -%} };
        

    this.userAuthenticated = {{ macros.jsboolean(request.user.authenticated) }};
    this.userName = "{{ request.user.name }}";
    this.userDisplayName = "{{ request.user.display_name }}";
    this.userCsrfToken = "{{ csrf_token("plain") }}";
}
