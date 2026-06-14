/**
 * Scarp — basemap registry.
 * Only open-access tile endpoints with acceptable licenses for public deploy.
 * No ESRI World Imagery / Maxar imagery (license issues).
 */

export interface Basemap {
  /** Unique identifier used as the map style key. */
  id: string;
  /** Full display name shown in tooltips. */
  name: string;
  /** Short name for compact UI buttons. */
  shortName: string;
  /** XYZ tile URL template(s) — standard {z}/{x}/{y} or {z}/{y}/{x} as required. */
  tiles: string[];
  tileSize: number;
  attribution: string;
  /** False when the tile service URL is unverified or not publicly accessible. */
  available: boolean;
}

export const BASEMAPS: Basemap[] = [
  {
    id: 'esri-topo',
    name: 'ESRI World Topo',
    shortName: 'Topo',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    attribution: 'Tiles &copy; Esri',
    available: true,
  },
  {
    id: 'usgs-topo',
    name: 'USGS Topo (National Map)',
    shortName: 'USGS Topo',
    tiles: [
      'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    attribution:
      'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>',
    available: true,
  },
  {
    id: 'usgs-imagery',
    name: 'USGS Imagery (National Map)',
    shortName: 'USGS Imagery',
    tiles: [
      'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    attribution:
      'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>',
    available: true,
  },
  {
    id: 'sentinel2',
    name: 'Sentinel-2 Cloudless 2021 (EOX)',
    shortName: 'Sentinel-2',
    tiles: [
      'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2021_3857/default/g/{z}/{y}/{x}.jpg',
    ],
    tileSize: 256,
    attribution:
      'Sentinel-2 cloudless &copy; <a href="https://eox.at/">EOX IT Services GmbH</a> (CC BY 4.0)',
    available: true,
  },
  {
    id: 'usgs-historical-topo',
    name: 'USGS Historical Topo (Esri archive)',
    shortName: 'Hist. Topo',
    // Esri/USGS historical topographic map archive (~1900–1990 US quads).
    tiles: [
      'https://historicalmaps.arcgis.com/arcgis/rest/services/Historical_Topos/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    attribution: 'USGS historical topo &copy; Esri',
    available: true,
  },
  {
    id: 'ahap',
    name: 'AHAP 1978–86 Historical (Alaska)',
    shortName: 'AHAP 1978',
    // UAF GINA AHAP tile service — URL requires verification before enabling.
    tiles: ['https://tiles.gina.alaska.edu/tilesrv/ahap_nb/tile/{z}/{x}/{y}'],
    tileSize: 256,
    attribution: 'AHAP imagery from <a href="https://gina.alaska.edu/">UAF GINA</a>',
    available: false, // ⚠️ tile service URL unverified — set true once confirmed
  },
];

export const DEFAULT_BASEMAP_ID = 'esri-topo';
