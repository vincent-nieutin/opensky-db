import { useState, useEffect } from "react";

export function useLocalStorage(key, initialValue) {
    const [value, setValue] = useState(() => {
        const stored = localStorage.getItem(key);
        const returnedValue = stored ? JSON.parse(stored) : initialValue;
        console.log(`Local Storage: Get ${key} = ${JSON.stringify(returnedValue)}`);
        return returnedValue;
    });

    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
        console.log(`Local Storage: Set ${key} to ${JSON.stringify(value)}`);
    }, [key, value]);

    return [value, setValue];
}