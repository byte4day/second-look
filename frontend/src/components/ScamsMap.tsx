import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const areaCenters: Record<string, [number, number]> = {
  generic: [54.5, -2.5],
  england: [52.5, -1.5],
  scotland: [56.5, -4],
  wales: [52.3, -3.8],
  northern_ireland: [54.6, -6.8],
}

interface ScamsMapProps {
  area: string
}

export function ScamsMap({ area }: ScamsMapProps) {
  const center = areaCenters[area] ?? areaCenters.generic

  return (
    <div className="map-wrap">
      <MapContainer center={center} zoom={6} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={center}>
          <Popup>Reports are anonymous. This pin shows the centre of your selected area.</Popup>
        </Marker>
      </MapContainer>
    </div>
  )
}