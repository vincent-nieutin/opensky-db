import { useEffect, useState, useRef } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Switch, FormControlLabel } from "@mui/material";
import { useLocalStorage } from "../hooks/useLocalStorage";

export default function FlightTable() {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useLocalStorage("page", 0);
    const [rowCount, setRowCount] = useState(0);
    const [cursorMap, setCursorMap] = useState({ 0: null });
    const [lastCursorSent, setLastCursorSent] = useState(null);
    const [filters, setFilters] = useLocalStorage("filters", {});
    const [pageSize, setPageSize] = useLocalStorage("pageSize", 25);
    const [sortModel, setSortModel] = useLocalStorage("sortModel", []);

    const [unitSystem, setUnitSystem] = useLocalStorage("unitSystem", "imperial");
    const metersToFeet = (m) => m * 3.28084;
    const metersPerSecondToKnots = (mps) => mps * 1.94384;

    const columns = [
        { field: "icao24", "headerName": "ICAO24", flex: 1 },
        { field: "callsign", headerName: "Callsign", flex: 1 },
        { field: "origin_country", headerName: "Country", flex: 1 },
        // { field: "time_position", headerName: "Time Position", flex: 1 },
        // { field: "last_contact", headerName: "Last Contact", flex: 1 },
        { field: "longitude", headerName: "Longitude", flex: 1 },
        { field: "latitude", headerName: "Latitude", flex: 1 },
        {
            field: "baro_altitude",
            headerName: "Altitude",
            flex: 1,
            valueFormatter: (value) => {
                if (value == null) return "-";
                return unitSystem === "imperial"
                    ? `${Math.round(metersToFeet(value)).toLocaleString()} ft`
                    : `${Math.round(value).toLocaleString()} m`
            }
        },
        {
            field: "on_ground",
            headerName: "On Ground",
            flex: 1,
            valueFormatter: (value) =>
                value === 1 ? "Yes" : value === 0 ? "No" : "-"
        },
        {
            field: "velocity",
            headerName: "Velocity",
            flex: 1,
            valueFormatter: (value) => {
                if (value == null) return "-";
                return unitSystem === "imperial"
                    ? `${metersPerSecondToKnots(value).toFixed(1)} kts`
                    : `${value.toFixed(1)} m/s`
            }
        },
        {
            field: "true_track",
            headerName: "True Track",
            flex: 1,
            renderCell: (params) => {
                const value = params.value;
                if (value === null) return "-";

                const angle = Math.round(value);
                const arrowStyle = {
                    display: "inline-block",
                    transform: `rotate(${angle}deg)`,
                    transition: "transfrom 0.2 ease",
                    marginRight: "15px",
                    fontSize: "25px"
                };

                return (
                    <div style={{ display: "flex", alignItems: "center" }}>
                        <span style={arrowStyle}>↑</span>
                        {`${angle.toLocaleString()}°`}
                    </div>
                )
            }
            // valueFormatter: (value) =>
            //     value != null ? `${value.toFixed(0)}°` : "—"
        },
        {
            field: "vertical_rate",
            headerName: "Vertical Rate",
            flex: 1,
            renderCell: (params) => {
                let value = params.value;
                if (value === null) value = 0;

                const arrowStyle = {
                    display: "inline-block",
                    fontSize: "23px"
                };

                return (
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-evenly" }}>
                        <span style={arrowStyle}>
                            {
                                value < 0
                                    ? "˅"
                                    : value > 0
                                    ? "˄"
                                    : " "
                            }
                            
                        </span>
                        {
                            unitSystem === "imperial"
                                ? `${Math.abs(metersPerSecondToKnots(value).toFixed(1))} ft/s`
                                : `${value.toFixed(1)} m/s`
                        }
                    </div>
                )
            },
        },
        // {
        //     field: "geo_altitude",
        //     headerName: "Geo Altitude",
        //     flex: 1,
        //     valueFormatter: (value) =>
        //         value != null ? `${value.toFixed(0)} m` : "—"
        // },
        { field: "squawk", headerName: "Squawk", flex: 1 },
        // { field: "position_source", headerName: "Position Source", flex: 1 },
        // { field: "category", headerName: "Category", flex: 1 }
    ];

    const socketRef = useRef(null);

    const sendPageRequest = (cursor, size = pageSize, model = sortModel) => {
        const sort = model[0] || {};

        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(
                JSON.stringify({
                    filters: filters,
                    page_size: size,
                    cursor: cursor,
                    sort_field: sort.field,
                    sort_order: sort.sort
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
            sendPageRequest(null);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

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

    useEffect(() => {
        sendPageRequest(null); // restart from beginning with new filters
    }, [filters]);

    const handlePageChange = (model) => {
        const newPage = model.page;
        const newPageSize = model.pageSize;

        setPageSize(newPageSize);
        const cursor = cursorMap[newPage] ?? lastCursorSent ?? null;
        setPage(newPage);
        sendPageRequest(cursor, newPageSize);
    };

    const handleSortChange = (newModel) => {
        setSortModel(newModel);
        setCursorMap({ 0: null });
        setPage(0);
        sendPageRequest(null, pageSize, newModel)
    };

    return (
        <div>
            <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                    <input
                        type="text"
                        placeholder="Search ICAO24"
                        value={filters.icao24 || ""}
                        onChange={(e) => {
                            const value = e.target.value;
                            setFilters((prev) => ({
                                ...prev,
                                icao24: value || undefined,
                            }));
                            setCursorMap({ 0: null });
                            setPage(0);
                        }}
                        style={{ padding: 8, width: 200 }}
                    />
                    <input
                        type="text"
                        placeholder="Search callsign"
                        value={filters.callsign || ""}
                        onChange={(e) => {
                            const value = e.target.value;
                            setFilters((prev) => ({
                                ...prev,
                                callsign: value || undefined,
                            }));
                            setCursorMap({ 0: null });
                            setPage(0);
                        }}
                        style={{ padding: 8, width: 200 }}
                    />
                    <input
                        type="text"
                        placeholder="Search Country"
                        value={filters.origin_country || ""}
                        onChange={(e) => {
                            const value = e.target.value;
                            setFilters((prev) => ({
                                ...prev,
                                origin_country: value || undefined,
                            }));
                            setCursorMap({ 0: null });
                            setPage(0);
                        }}
                        style={{ padding: 8, width: 200 }}
                    />
                    <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        On Ground:
                        <select
                            value={
                                filters.on_ground === 1
                                    ? "yes"
                                    : filters.on_ground === 0
                                        ? "no"
                                        : "any"
                            }
                            onChange={(e) => {
                                const value = e.target.value;
                                setFilters((prev) => ({
                                    ...prev,
                                    on_ground:
                                        value === "any" ? undefined : value === "yes" ? 1 : 0
                                }));
                                setCursorMap({ 0: null });
                                setPage(0);
                            }}
                            style={{
                                padding: "8px",
                                borderRadius: "4px",
                                border: "1px solid #ccc",
                                backgroundColor: "#fff"
                            }}
                        >
                            <option value="any">Any</option>
                            <option value="yes">Yes</option>
                            <option value="no">No</option>
                        </select>
                    </label>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={Array.isArray(filters.squawk)}
                                onChange={(e) => {
                                    const checked = e.target.checked;
                                    setFilters((prev) => ({
                                        ...prev,
                                        squawk: checked ? ["7500", "7600", "7700"] : undefined,
                                    }));
                                    setCursorMap({ 0: null });
                                    setPage(0);
                                }}
                            />
                        }
                        label="Emergencies"
                    />
                </div>
                <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span>Metric</span>
                    <Switch
                        checked={unitSystem === "imperial"}
                        onChange={(e) => {
                            setUnitSystem(e.target.checked ? "imperial" : "metric"); // new state
                        }}
                    />
                    <span>Imperial</span>
                </label>
            </div>
            <div style={{ height: "calc(100vh - 94px)", width: "100%" }}>
                <DataGrid
                    sx={{
                        "& .MuiDataGrid-row:hover": {
                            backgroundColor: "#f0f8ff",
                            cursor: "pointer"
                        }
                    }}
                    rows={rows}
                    columns={columns}
                    getRowId={(row) => row.id}
                    loading={loading}
                    sortModel={sortModel}
                    sortingMode="server"
                    onSortModelChange={handleSortChange}
                    pagination
                    paginationMode="server"
                    onPaginationModelChange={handlePageChange}
                    rowCount={rowCount}
                    pageSize={pageSize}
                    pageSizeOptions={[5, 10, 25, 50, 100]}
                    page={page}
                    initialState={{
                        pagination: {
                            paginationModel: {
                                pageSize: pageSize,
                                page: page
                            }
                        }
                    }}
                    onRowClick={(params) => {
                        const icao = params.row.icao24;
                        if (icao) {
                            window.open(`https://globe.adsbexchange.com/?icao=${icao}`, "_blank");
                        }
                    }}
                />
            </div>
        </div>
    );
}