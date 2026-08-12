import { useState, useCallback } from "react";

export type GeolocationStatus =
  | "idle"
  | "requesting"
  | "success"
  | "denied"
  | "unavailable"
  | "error";

export interface GeolocationState {
  status: GeolocationStatus;
  latitude: number | null;
  longitude: number | null;
  errorMessage: string | null;
}

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>({
    status: "idle",
    latitude: null,
    longitude: null,
    errorMessage: null,
  });

  const requestLocation = useCallback(() => {
    if (typeof window === "undefined" || !("geolocation" in navigator)) {
      setState({
        status: "unavailable",
        latitude: null,
        longitude: null,
        errorMessage: "Location services are unavailable on this browser.",
      });
      return;
    }

    setState({
      status: "requesting",
      latitude: null,
      longitude: null,
      errorMessage: null,
    });

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = Math.round(position.coords.latitude * 1000000) / 1000000;
        const lng = Math.round(position.coords.longitude * 1000000) / 1000000;
        setState({
          status: "success",
          latitude: lat,
          longitude: lng,
          errorMessage: null,
        });
      },
      (err) => {
        let msg = "Unable to determine your location.";
        let status: GeolocationStatus = "error";

        if (err.code === err.PERMISSION_DENIED) {
          status = "denied";
          msg = "Location permission was denied. You can enter your location manually.";
        } else if (err.code === err.POSITION_UNAVAILABLE) {
          status = "unavailable";
          msg = "Location information is unavailable.";
        } else if (err.code === err.TIMEOUT) {
          status = "error";
          msg = "Location request timed out. Please try again or enter location manually.";
        }

        setState({
          status,
          latitude: null,
          longitude: null,
          errorMessage: msg,
        });
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000,
      }
    );
  }, []);

  const clearLocation = useCallback(() => {
    setState({
      status: "idle",
      latitude: null,
      longitude: null,
      errorMessage: null,
    });
  }, []);

  return {
    ...state,
    requestLocation,
    clearLocation,
  };
}
