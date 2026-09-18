import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
import { authApi } from "@/api";
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from "@/api/client";
import type { User, UserRole } from "@/types";

interface AuthState {
  user: User | null;
  status: "idle" | "loading" | "authenticated" | "error";
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  status: "idle",
  error: null,
};

export const login = createAsyncThunk(
  "auth/login",
  async (payload: { email: string; password: string; totp_code?: string }, { rejectWithValue }) => {
    try {
      const tokens = await authApi.login(payload);
      localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
      const user = await authApi.me();
      return user;
    } catch (err: any) {
      return rejectWithValue(err?.response?.data?.detail || 'Something went wrong');
    }
  }
);

export const register = createAsyncThunk(
  "auth/register",
  async (payload: { email: string; password: string; full_name: string; role: UserRole; referral_code?: string }, { rejectWithValue }) => {
    try {
      await authApi.register(payload);
      const tokens = await authApi.login({ email: payload.email, password: payload.password });
      localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
      const user = await authApi.me();
      return user;
    } catch (err: any) {
      return rejectWithValue(err?.response?.data?.detail || 'Something went wrong');
    }
  }
);

export const fetchCurrentUser = createAsyncThunk("auth/fetchCurrentUser", async () => {
  return await authApi.me();
});

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    logout(state) {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      state.user = null;
      state.status = "idle";
    },
    setUser(state, action: PayloadAction<User>) {
      state.user = action.payload;
      state.status = "authenticated";
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = "authenticated";
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message ?? "Login failed";
      })
      .addCase(register.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.status = "authenticated";
        state.user = action.payload;
      })
      .addCase(register.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message ?? "Registration failed";
      })
      .addCase(fetchCurrentUser.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.status = "authenticated";
        state.user = action.payload;
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        state.status = "idle";
        state.user = null;
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      });
  },
});

export const { logout, setUser } = authSlice.actions;
export default authSlice.reducer;
