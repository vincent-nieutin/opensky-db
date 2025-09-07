import { useState, useEffect } from "react";

export function useDebouncedValue(value, delay = 300) {
    const [debounced, setDebounced] = useState(value);

    useEffect(() => {
        const handler = setTimeout(() => setDebounced(value), delay);
        return () => clearTimeout(handler)
    }, [value, delay]);

    return debounced;
}