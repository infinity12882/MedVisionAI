import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

interface UiState {
  darkMode: boolean;
  language: "en" | "uz" | "ru";
}

function getInitialDarkMode(): boolean {
  const stored = localStorage.getItem("medvision_dark_mode");
  if (stored !== null) return stored === "true";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

const initialState: UiState = {
  darkMode: getInitialDarkMode(),
  language: (localStorage.getItem("medvision_language") as UiState["language"]) || "en",
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleDarkMode(state) {
      state.darkMode = !state.darkMode;
      localStorage.setItem("medvision_dark_mode", String(state.darkMode));
    },
    setDarkMode(state, action: PayloadAction<boolean>) {
      state.darkMode = action.payload;
      localStorage.setItem("medvision_dark_mode", String(state.darkMode));
    },
    setLanguage(state, action: PayloadAction<UiState["language"]>) {
      state.language = action.payload;
      localStorage.setItem("medvision_language", action.payload);
    },
  },
});

export const { toggleDarkMode, setDarkMode, setLanguage } = uiSlice.actions;
export default uiSlice.reducer;
