import { useEffect, useState, useMemo, useCallback } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Switch, FormControlLabel } from "@mui/material";
import { useLocalStorage } from "../hooks/useLocalStorage";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useWebSocketRequest } from "../hooks/useWebSocketRequest";

// ─── Constants & Helpers 

const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const API_WS_URL = `${protocol}://${window.location.host}/ws`;

const metersToFeet = (m) => m * 3.28084;
const metersPerSecondToKnots = (mps) => mps * 1.94384;

const containerStyle = { marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" };
const filterGroupStyle = { display: "flex", gap: "12px", alignItems: "center" }

// ─── Component

export default function FlightTable() {
    // Core state
    const [rows, setRows] = useState([]);
    const [rowCount, setRowCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [cursorMap, setCursorMap] = useState({ 0: null });
    const [lastCursorSent, setLastCursorSent] = useState(null);

    // Persisted state
    const [page, setPage] = useLocalStorage("page", 0);
    const [pageSize, setPageSize] = useLocalStorage("pageSize", 25);
    const [sortModel, setSortModel] = useLocalStorage("sortModel", []);
    const [filters, setFilters] = useLocalStorage("filters", {});
    const [unitSystem, setUnitSystem] = useLocalStorage("unitSystem", "imperial");

    // Debounced inputs
    const [rawFilters, setRawFilters] = useState(filters);
    const debouncedFilters = useDebouncedValue(rawFilters, 300);

    // ─── WebSocket hook

    const handleServerMessage = useCallback(data => {
        if (data.error) {
            console.error("Server error:", data.error);
            setLoading(false);
            return;
        }

        setRows(data.results);
        setRowCount(data.results_count);
        setLoading(false);

        setCursorMap(prev => ({
            ...prev,
            [Object.keys(prev).length]: data.next_cursor,
        }));
        setLastCursorSent(data.next_cursor);
    }, []);

    const { sendRequest, isReady } = useWebSocketRequest(API_WS_URL, handleServerMessage);

    // ─── Memoized columns

    const columns = useMemo(() => [
        { field: "icao24", "headerName": "ICAO24", flex: 1 },
        { field: "callsign", headerName: "Callsign", flex: 1 },
        { field: "origin_country", headerName: "Country", flex: 1 },
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
            renderCell: ({ value }) => {
                if (value == null) return "-";
                const angle = Math.round(value);
                const arrowStyle = {
                    display: "inline-block",
                    transform: `rotate(${angle}deg)`,
                    marginRight: 15,
                    fontSize: 25
                };
                return (
                    <div style={{ display: "flex", alignItems: "center" }}>
                        <span style={arrowStyle}>↑</span>
                        {angle.toLocaleString()}°
                    </div>
                );
            }
        },
        {
            field: "vertical_rate",
            headerName: "Vertical Rate",
            flex: 1,
            renderCell: ({ value: raw }) => {
                const value = raw == null ? 0 : raw;
                // const arrow = value < 0 ? "˅" : value > 0 ? "˄" : " ";
                return (
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-evenly" }}>
                        {/* <span style={{ fontSize: 23 }}>{arrow}</span> */}
                        {unitSystem === "imperial"
                            ? `${metersPerSecondToKnots(value).toFixed(1)} ft/s`
                            : `${value.toFixed(1)} m/s`}
                    </div>
                );
            }
        },
        { field: "squawk", headerName: "Squawk", flex: 1 },
    ], [unitSystem]);

    // ─── sendPageRequest Callback

    const sendPageRequest = useCallback(
        (cursor = null) => {
            const { field, sort } = sortModel[0] || {};
            setLoading(true);
            sendRequest({
                filters,
                page_size: pageSize,
                cursor,
                sort_field: field,
                sort_order: sort
            });
            setLastCursorSent(cursor);
        },
        [filters, pageSize, sortModel, sendRequest]
    );

    // ─── Effects

    // 1) On first WS‐ready, fire initial request
    useEffect(() => {
        if (isReady) {
            sendPageRequest(null);
        };
    }, [isReady, sendPageRequest]);

    // 2) When debounced filters change, reset pagination + request
    useEffect(() => {
        if (!isReady) return

        setCursorMap({ 0: null });
        setPage(0);
        setFilters(debouncedFilters);
        sendPageRequest(null)
    }, [debouncedFilters, isReady, setFilters, setPage, sendPageRequest]);

    // ─── Handlers

    const handlePageChange = useCallback(
        ({ page: newPage, pageSize: newPageSize }) => {
            setPage(newPage);
            setPageSize(newPageSize);
            const cursor = cursorMap[newPage] ?? lastCursorSent;
            sendPageRequest(cursor);
        },
        [cursorMap, lastCursorSent, sendPageRequest, setPage, setPageSize]
    );

    const handleSortChange = useCallback(
        (newModel) => {
            setSortModel(newModel);
            setPage(0);
            setCursorMap({ 0: null });
            sendPageRequest(null);
        },
        [sendPageRequest, setSortModel, setPage, setCursorMap]
    );

    // ─── Render

    return (
        <div>
            <div style={containerStyle}>
                <div style={filterGroupStyle}>
                    <input
                        type="text"
                        placeholder="Search ICAO24"
                        value={rawFilters.icao24 || ""}
                        onChange={e => setRawFilters((prev) => ({ ...prev, icao24: e.target.value || undefined }))}
                        style={{ padding: 8, width: 200 }}
                    />
                    <input
                        type="text"
                        placeholder="Search callsign"
                        value={rawFilters.callsign || ""}
                        onChange={e => setRawFilters(prev => ({ ...prev, callsign: e.target.value || undefined }))}
                        style={{ padding: 8, width: 200 }}
                    />
                    <input
                        type="text"
                        placeholder="Search Country"
                        value={rawFilters.origin_country || ""}
                        onChange={e => setRawFilters(prev => ({ ...prev, origin_country: e.target.value || undefined }))}
                        style={{ padding: 8, width: 200 }}
                    />

                    <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        On Ground:
                        <select
                            value={
                                rawFilters.on_ground === 1
                                    ? "yes"
                                    : rawFilters.on_ground === 0
                                        ? "no"
                                        : "any"
                            }
                            onChange={e =>
                                setRawFilters(prev => ({
                                    ...prev,
                                    on_ground:
                                        e.target.value === "any"
                                            ? undefined
                                            : e.target.value === "yes"
                                                ? 1
                                                : 0
                                }))
                            }
                            style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc", backgroundColor: "#fff" }}
                        >
                            <option value="any">Any</option>
                            <option value="yes">Yes</option>
                            <option value="no">No</option>
                        </select>
                    </label>

                    <FormControlLabel
                        control={
                            <Switch
                                checked={Array.isArray(rawFilters.squawk)}
                                onChange={e =>
                                    setRawFilters(prev => ({
                                        ...prev,
                                        squawk: e.target.checked ? ["7500", "7600", "7700"] : undefined
                                    }))
                                }
                            />
                        }
                        label="Emergencies"
                    />
                </div>

                <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span>Metric</span>
                    <Switch
                        checked={unitSystem === "imperial"}
                        onChange={e => setUnitSystem(e.target.checked ? "imperial" : "metric")}
                    />
                    <span>Imperial</span>
                </label>
            </div>

            <div style={{ height: "calc(100vh - 94px)", width: "100%" }}>
                <DataGrid
                    rows={rows}
                    columns={columns}
                    getRowId={r => r.id}
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
                        pagination: { paginationModel: { pageSize: pageSize, page: page } }
                    }}
                    sx={{
                        "& .MuiDataGrid-row:hover": {
                            backgroundColor: "#f0f8ff",
                            cursor: "pointer"
                        }
                    }}
                    onRowClick={params => {
                        const icao = params.row.icao24;
                        if (icao) window.open(`https://globe.adsbexchange.com/?icao=${icao}`, "_blank");
                    }}
                />
            </div>
        </div>
    );
}