import React, { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";

const columns = [
    { field: "icao24", "headerName": "ICAO24", flex: 1 },
    { field: "callsign", headerName: "Callsign", flex: 1 },
    { field: "origin_country", headerName: "Country", flex: 1 },
    { field: "time_position", headerName: "Time Position", flex: 1 },
    { field: "last_contact", headerName: "Last Contact", flex: 1 },
    { field: "longitude", headerName: "Longitude", flex: 1 },
    { field: "latitude", headerName: "Latitude", flex: 1 },
    { field: "baro_altitude", headerName: "Baro Altitude", flex: 1 },
    { field: "on_ground", headerName: "On Ground", flex: 1 },
    { field: "velocity", headerName: "Velocity", flex: 1 },
    { field: "true_track", headerName: "True Track", flex: 1 },
    { field: "vertical_rate", headerName: "Vertical Rate", flex: 1 },
    { field: "geo_altitude", headerName: "Geo Altitude", flex: 1 },
    { field: "squawk", headerName: "Squawk", flex: 1 },
    { field: "position_source", headerName: "Position Source", flex: 1 },
    { field: "category", headerName: "Category", flex: 1 }
];

export default function FlightTable() {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchFlights = async () => {
        setLoading(true);
        const res = await fetch("http://localhost:8000/");
        const data = await res.json();
        setRows(data.results);
        setLoading(false);
    };

    useEffect(() => {
        fetchFlights();
        const interval = setInterval(fetchFlights, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div style={{ height: 600, width: "100%" }}>
            <DataGrid
                rows={rows}
                columns={columns}
                getRowId={(row) => row.id}
                loading={loading}
                pagination
                pageSizeOptions={[50]}
            />
        </div>
    );
}