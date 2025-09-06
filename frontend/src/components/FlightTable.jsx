import React, { useEffect, useState, useRef } from "react";
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
    const [page, setPage] = useState(0);
    const [rowCount, setRowCount] = useState(0);
    const [cursorMap, setCursorMap] = useState({ 0: null });
    const [lastCursorSent, setLastCursorSent] = useState(null);

    const socketRef = useRef(null);

    const sendPageRequest = (cursor) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(
                JSON.stringify({
                    filters: {},
                    page_size: 50,
                    cursor: cursor,
                })
            );
            setLoading(true);
            setLastCursorSent(cursor);
        }
    };

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8000/ws");
        socketRef.current = socket;

        socket.onopen = () => {
            console.log("WebSocket connection established");
            sendPageRequest(0);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("Received data:", data);

            if (data.error) {
                console.error("Server error:", data.error);
                setLoading(false);
                return;
            }

            setRows(data.results);
            setRowCount(data.results_count);
            setLoading(false);

            setCursorMap((prev) => {
                const nextPage = Object.keys(prev).length;
                return {
                    ...prev,
                    [nextPage]: data.next_cursor,
                };
            });
            setLastCursorSent(data.next_cursor);
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        socket.onclose = () => {
            console.log("WebSocket connection closed");
        };

        return () => {
            if (
                socket.readyState === WebSocket.OPEN ||
                socket.readyState === WebSocket.CONNECTING
            ) {
                socket.close(1000, "Component unmounted");
            }
        };
    }, []);

    const handlePageChange = (model) => {
        const newPage = model.page
        console.log("Page changed to:", newPage);

        const cursor = cursorMap[newPage] ?? lastCursorSent ?? null;
        setPage(newPage);
        sendPageRequest(cursor);
    };

    return (
        <div style={{ height: 600, width: "100%" }}>
            <DataGrid
                rows={rows}
                columns={columns}
                getRowId={(row) => row.id}
                loading={loading}
                pagination
                paginationMode="server"
                rowCount={rowCount}
                pageSize={50}
                pageSizeOptions={[50]}
                page={page}
                onPaginationModelChange={handlePageChange}
            />
        </div>
    );
}