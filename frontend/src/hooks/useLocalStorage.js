import { useState, useEffect } from "react";

export function useLocalStorage(key, initialValue) {
    const [value, setValue] = useState(() => {
        const stored = localStorage.getItem(key);
        const returnedValue = stored ? JSON.parse(stored) : initialValue;
        return returnedValue;
    });

    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
    }, [key, value]);

    return [value, setValue];
}