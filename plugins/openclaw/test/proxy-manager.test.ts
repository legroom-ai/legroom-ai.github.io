import { describe, it, expect, afterEach, vi } from "vitest";
import {
  ProxyManager,
  normalizeAndValidateProxyUrl,
  isLocalProxyUrl,
  probeLegroomProxy,
} from "../src/proxy-manager.js";

const retrieveStatsBody = JSON.stringify({ store: { entry_count: 0 }, recent_retrievals: [] });
const proxyStatsBody = JSON.stringify({ proxy_inbound: { total: 1 } });

afterEach(() => {
  vi.restoreAllMocks();
});

function stubProbeSuccess() {
  const mock = vi
    .fn()
    .mockResolvedValueOnce({ ok: false, status: 404 }) // /readyz
    .mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: () => Promise.resolve(retrieveStatsBody),
    }); // /v1/retrieve/stats
  vi.stubGlobal("fetch", mock);
  return mock;
}

function stubProbeNonLegroom() {
  // Every endpoint reachable but non-OK => reachable, non-Legroom (occupied port).
  const mock = vi.fn().mockResolvedValue({ ok: false, status: 404 });
  vi.stubGlobal("fetch", mock);
  return mock;
}

function stubProbeUnreachable() {
  const mock = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));
  vi.stubGlobal("fetch", mock);
  return mock;
}

describe("normalizeAndValidateProxyUrl", () => {
  it("accepts localhost origins", () => {
    expect(normalizeAndValidateProxyUrl("http://127.0.0.1:8787")).toBe("http://127.0.0.1:8787");
    expect(normalizeAndValidateProxyUrl("http://localhost:8787")).toBe("http://localhost:8787");
  });

  it("accepts remote URLs", () => {
    expect(normalizeAndValidateProxyUrl("http://example.com:8787")).toBe("http://example.com:8787");
    expect(normalizeAndValidateProxyUrl("https://legroom.example.com")).toBe("https://legroom.example.com");
    expect(normalizeAndValidateProxyUrl("https://legroom.example.com:9090")).toBe("https://legroom.example.com:9090");
  });

  it("rejects malformed URLs", () => {
    expect(() => normalizeAndValidateProxyUrl("ftp://localhost:8787")).toThrow(
      /must use http/,
    );
    expect(() => normalizeAndValidateProxyUrl("http://localhost:8787/path")).toThrow(
      /must not include a path/,
    );
  });
});

describe("isLocalProxyUrl", () => {
  it("returns true for localhost addresses", () => {
    expect(isLocalProxyUrl("http://127.0.0.1:8787")).toBe(true);
    expect(isLocalProxyUrl("http://localhost:8787")).toBe(true);
  });

  it("returns false for remote addresses", () => {
    expect(isLocalProxyUrl("http://example.com:8787")).toBe(false);
    expect(isLocalProxyUrl("https://legroom.example.com")).toBe(false);
  });

  it("returns false for invalid URLs", () => {
    expect(isLocalProxyUrl("not-a-url")).toBe(false);
  });
});

describe("probeLegroomProxy", () => {
  /**
   * Resolve fetch outcomes by request path so tests express the new probe order
   * (/readyz, /v1/retrieve/stats, /stats, /health) without depending on call
   * sequencing. Unlisted paths reject (treated as unreachable).
   */
  function stubByPath(byPath: Record<string, { ok: boolean; status: number; body?: string }>) {
    const mock = vi.fn((url: string) => {
      for (const [path, response] of Object.entries(byPath)) {
        if (url.endsWith(path)) {
          return Promise.resolve({
            ok: response.ok,
            status: response.status,
            text: () => Promise.resolve(response.body ?? ""),
          });
        }
      }
      return Promise.reject(new Error("ECONNREFUSED"));
    });
    vi.stubGlobal("fetch", mock);
    return mock;
  }

  it("does not treat /readyz success alone as Legroom identity", async () => {
    stubByPath({
      "/readyz": { ok: true, status: 200 },
      "/v1/retrieve/stats": { ok: false, status: 404 },
      "/stats": { ok: false, status: 404 },
      "/health": { ok: false, status: 404 },
    });
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result.reachable).toBe(true);
    expect(result.isLegroom).toBe(false);
  });

  it("treats Legroom-shaped /v1/retrieve/stats 200 as Legroom even when /readyz is OK and /health is 503", async () => {
    stubByPath({
      "/health": { ok: false, status: 503 },
      "/readyz": { ok: true, status: 200 },
      "/v1/retrieve/stats": { ok: true, status: 200, body: retrieveStatsBody },
    });
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result).toEqual({ reachable: true, isLegroom: true });
  });

  it("treats Legroom-shaped /v1/retrieve/stats 200 as Legroom even when /health is 503", async () => {
    stubByPath({
      "/health": { ok: false, status: 503 },
      "/readyz": { ok: false, status: 404 },
      "/v1/retrieve/stats": { ok: true, status: 200, body: retrieveStatsBody },
    });
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result).toEqual({ reachable: true, isLegroom: true });
  });

  it("does not treat generic /v1/retrieve/stats 200 as Legroom identity", async () => {
    stubByPath({
      "/readyz": { ok: true, status: 200 },
      "/v1/retrieve/stats": { ok: true, status: 200, body: JSON.stringify({ ok: true }) },
      "/stats": { ok: false, status: 404 },
      "/health": { ok: true, status: 200 },
    });
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result.reachable).toBe(true);
    expect(result.isLegroom).toBe(false);
  });

  it("falls through from auth-gated /v1/retrieve/stats to Legroom-shaped /stats", async () => {
    stubByPath({
      "/readyz": { ok: true, status: 200 },
      "/v1/retrieve/stats": { ok: false, status: 403 },
      "/stats": { ok: true, status: 200, body: proxyStatsBody },
    });
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result).toEqual({ reachable: true, isLegroom: true });
  });

  it("continues probing when one endpoint is unreachable", async () => {
    stubByPath({
      "/readyz": { ok: true, status: 200 },
      // /v1/retrieve/stats rejects because it is not listed.
      "/stats": { ok: true, status: 200, body: proxyStatsBody },
    });
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result).toEqual({ reachable: true, isLegroom: true });
  });

  it("falls back to /stats only when the response has a Legroom stats shape", async () => {
    stubByPath({
      // /readyz and /v1/retrieve/stats unavailable (reject), /stats answers.
      "/stats": { ok: true, status: 200, body: proxyStatsBody },
    });
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result).toEqual({ reachable: true, isLegroom: true });
  });

  it("does not treat generic /stats 200 as Legroom identity", async () => {
    stubByPath({
      "/readyz": { ok: false, status: 404 },
      "/v1/retrieve/stats": { ok: false, status: 404 },
      "/stats": { ok: true, status: 200, body: JSON.stringify({ uptime: 123 }) },
      "/health": { ok: true, status: 200 },
    });
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result.reachable).toBe(true);
    expect(result.isLegroom).toBe(false);
  });

  it("returns reachable but non-legroom when identity endpoints are non-OK", async () => {
    stubProbeNonLegroom();
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result.reachable).toBe(true);
    expect(result.isLegroom).toBe(false);
    expect(result.reason).toMatch(/retrieve stats HTTP 404/);
  });

  it("returns unreachable when no endpoint responds", async () => {
    stubProbeUnreachable();
    const result = await probeLegroomProxy("http://127.0.0.1:8787");
    expect(result.reachable).toBe(false);
    expect(result.isLegroom).toBe(false);
  });
});

describe("ProxyManager.start", () => {
  it("auto-detects running proxy on default candidates", async () => {
    const manager = new ProxyManager({});

    // Candidate 1 (127.0.0.1): all four probes fail.
    // Candidate 2 (localhost): /v1/retrieve/stats succeeds.
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error("down")) // 127.0.0.1 /readyz
      .mockRejectedValueOnce(new Error("down")) // 127.0.0.1 /v1/retrieve/stats
      .mockRejectedValueOnce(new Error("down")) // 127.0.0.1 /stats
      .mockRejectedValueOnce(new Error("down")) // 127.0.0.1 /health
      .mockResolvedValueOnce({ ok: true, status: 200 }) // localhost /readyz
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: () => Promise.resolve(retrieveStatsBody),
      }); // localhost /v1/retrieve/stats
    vi.stubGlobal("fetch", fetchMock);

    const startSpy = vi.spyOn(manager as any, "startLegroomProxy");
    const url = await manager.start();
    expect(url).toBe("http://localhost:8787");
    expect(startSpy).not.toHaveBeenCalled();
  });

  it("uses proxyPort for auto-detect candidates", async () => {
    const manager = new ProxyManager({ proxyPort: 9797, autoStart: false });

    const fetchMock = vi.fn().mockRejectedValue(new Error("down"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(manager.start()).rejects.toThrow(/127\.0\.0\.1:9797.*localhost:9797/);
  });

  it("rejects invalid proxyPort", async () => {
    const manager = new ProxyManager({ proxyPort: 0 });
    await expect(manager.start()).rejects.toThrow(/proxyPort must be an integer between 1 and 65535/);
  });

  it("fails when explicit URL is reachable but not a legroom proxy", async () => {
    const manager = new ProxyManager({ proxyUrl: "http://127.0.0.1:8787" });
    stubProbeNonLegroom();
    await expect(manager.start()).rejects.toThrow(/does not appear to be a Legroom proxy/);
  });

  it("applies default proxyPort when explicit proxyUrl omits port", async () => {
    const manager = new ProxyManager({ proxyUrl: "http://127.0.0.1", autoStart: true });
    const startSpy = vi.spyOn(manager as any, "startLegroomProxy").mockResolvedValue(undefined);

    // Initial probe of the single candidate fails on all four endpoints, then
    // after auto-start the identity probe succeeds on /v1/retrieve/stats.
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error("down")) // /readyz
      .mockRejectedValueOnce(new Error("down")) // /v1/retrieve/stats
      .mockRejectedValueOnce(new Error("down")) // /stats
      .mockRejectedValueOnce(new Error("down")) // /health
      .mockResolvedValueOnce({ ok: true, status: 200 }) // post-start /readyz
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: () => Promise.resolve(retrieveStatsBody),
      }); // post-start /v1/retrieve/stats
    vi.stubGlobal("fetch", fetchMock);

    const url = await manager.start();
    expect(url).toBe("http://127.0.0.1:8787");
    expect(startSpy).toHaveBeenCalledWith("http://127.0.0.1:8787", 8787);
  });

  it("connects to remote proxy without auto-start", async () => {
    const manager = new ProxyManager({ proxyUrl: "http://legroom.remote.example:8787", autoStart: true });
    const startSpy = vi.spyOn(manager as any, "startLegroomProxy").mockResolvedValue(undefined);
    stubProbeSuccess();

    const url = await manager.start();
    expect(url).toBe("http://legroom.remote.example:8787");
    expect(startSpy).not.toHaveBeenCalled();
  });

  it("does not apply proxyPort default to remote URLs", async () => {
    const manager = new ProxyManager({ proxyUrl: "https://legroom.remote.example", proxyPort: 9999 });
    stubProbeSuccess();

    const url = await manager.start();
    expect(url).toBe("https://legroom.remote.example");
  });

  it("fails fast for unreachable remote proxy without attempting auto-start", async () => {
    const manager = new ProxyManager({ proxyUrl: "https://legroom.remote.example:8787", autoStart: true });
    const startSpy = vi.spyOn(manager as any, "startLegroomProxy").mockResolvedValue(undefined);
    stubProbeUnreachable();

    await expect(manager.start()).rejects.toThrow(/Remote Legroom proxy not reachable/);
    expect(startSpy).not.toHaveBeenCalled();
  });

  it("auto-starts when nothing is detected", async () => {
    const manager = new ProxyManager({ autoStart: true });
    const startSpy = vi.spyOn(manager as any, "startLegroomProxy").mockResolvedValue(undefined);

    // Both candidates fail all four probes, then the post-start identity probe
    // succeeds on /v1/retrieve/stats.
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error("down")) // 127.0.0.1 /readyz
      .mockRejectedValueOnce(new Error("down")) // 127.0.0.1 /v1/retrieve/stats
      .mockRejectedValueOnce(new Error("down")) // 127.0.0.1 /stats
      .mockRejectedValueOnce(new Error("down")) // 127.0.0.1 /health
      .mockRejectedValueOnce(new Error("down")) // localhost /readyz
      .mockRejectedValueOnce(new Error("down")) // localhost /v1/retrieve/stats
      .mockRejectedValueOnce(new Error("down")) // localhost /stats
      .mockRejectedValueOnce(new Error("down")) // localhost /health
      .mockResolvedValueOnce({ ok: true, status: 200 }) // post-start /readyz
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: () => Promise.resolve(retrieveStatsBody),
      }); // post-start /v1/retrieve/stats
    vi.stubGlobal("fetch", fetchMock);

    const url = await manager.start();
    expect(url).toBe("http://127.0.0.1:8787");
    expect(startSpy).toHaveBeenCalledWith("http://127.0.0.1:8787", 8787);
  });
});

describe("ProxyManager launch internals", () => {
  it("prefers configured pythonPath in fallback order", () => {
    const manager = new ProxyManager({ pythonPath: "C:\\Python311\\python.exe" });
    const commands = (manager as any).getPythonCommands() as string[];
    expect(commands[0]).toBe("C:\\Python311\\python.exe");
    expect(commands).toContain("python");
    expect(commands).toContain("python3");
    expect(commands).toContain("py");
  });

  it("prefers configured pythonPath ahead of PATH launchers", () => {
    const manager = new ProxyManager({ pythonPath: "C:\\Python311\\python.exe" });
    vi.spyOn(manager as any, "getPyenvResolvedLegroom").mockReturnValue(null);

    const specs = (manager as any).buildLaunchSpecs("127.0.0.1", "8787") as Array<Record<string, unknown>>;

    expect(specs[0]?.label).toContain("Configured Python:");
    expect(specs[0]?.command).toBe("C:\\Python311\\python.exe");
    expect(specs[0]?.args).toEqual(["-m", "legroom.cli", "proxy", "--host", "127.0.0.1", "--port", "8787"]);
  });

  it("uses lightweight PATH checks instead of booting the legroom CLI", () => {
    const manager = new ProxyManager({});
    const specs = (manager as any).buildLaunchSpecs("127.0.0.1", "8787") as Array<Record<string, unknown>>;
    const pathSpec = specs.find((spec) => spec.command === "legroom");

    expect(pathSpec).toBeDefined();
    expect(pathSpec.command).toBe("legroom");
    expect(pathSpec.args).toEqual(["proxy", "--host", "127.0.0.1", "--port", "8787"]);
    if (process.platform === "win32") {
      expect(pathSpec.checkCommand).toBe("where.exe");
      expect(pathSpec.checkArgs).toEqual(["legroom"]);
      expect(pathSpec.checkUseShell).toBe(false);
    } else {
      expect(pathSpec.checkCommand).toBe("sh");
      expect(pathSpec.checkArgs).toEqual(["-lc", "command -v legroom >/dev/null 2>&1"]);
    }
  });

  it("prefers a resolved pyenv executable on Windows before PATH shims", () => {
    if (process.platform !== "win32") return;

    const manager = new ProxyManager({});
    vi.spyOn(manager as any, "getPyenvResolvedLegroom").mockReturnValue("C:\\Python312\\Scripts\\legroom.exe");

    const specs = (manager as any).buildLaunchSpecs("127.0.0.1", "8787") as Array<Record<string, unknown>>;

    expect(specs[0]?.label).toContain("pyenv:");
    expect(specs[0]?.command).toBe("C:\\Python312\\Scripts\\legroom.exe");
    expect(specs[0]?.useShell).toBe(false);
    expect(specs[1]?.command).toBe("legroom");
  });

  it("passes through fast-fail launch flags when configured", () => {
    const manager = new ProxyManager({ retryMaxAttempts: 1, connectTimeoutSeconds: 3 });
    const specs = (manager as any).buildLaunchSpecs("127.0.0.1", "8787") as Array<Record<string, unknown>>;
    const pathSpec = specs[0];

    expect(pathSpec.args).toEqual([
      "proxy",
      "--host",
      "127.0.0.1",
      "--port",
      "8787",
      "--retry-max-attempts",
      "1",
      "--connect-timeout-seconds",
      "3",
    ]);
  });

  it("uses lightweight module discovery for python fallback checks", () => {
    const manager = new ProxyManager({ pythonPath: "C:\\Python311\\python.exe" });
    const specs = (manager as any).buildLaunchSpecs("127.0.0.1", "8787") as Array<Record<string, unknown>>;
    const pythonSpec = specs.find((spec) => spec.command === "C:\\Python311\\python.exe");

    expect(pythonSpec).toBeDefined();
    expect(pythonSpec?.checkArgs).toEqual([
      "-c",
      "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('legroom') else 1)",
    ]);
  });

  it("uses first available launcher from provided specs", async () => {
    const manager = new ProxyManager({});
    (manager as any).buildLaunchSpecs = () => [
      {
        label: "first",
        command: "first-missing-command",
        args: ["proxy"],
        checkCommand: "first-missing-command",
        checkArgs: ["--version"],
      },
      {
        label: "second-node",
        command: "node",
        args: ["-e", ""],
        checkCommand: "node",
        checkArgs: ["--version"],
      },
    ];
    const infoSpy = vi.spyOn((manager as any).logger, "info");

    await (manager as any).startLegroomProxy("http://127.0.0.1:8787");
    expect(infoSpy).toHaveBeenCalledWith(expect.stringContaining("Auto-start launcher selected"));
    expect(infoSpy).toHaveBeenCalledWith(expect.stringContaining("second-node"));
  });

  it("supports shell-backed launch specs for PATH shims and script wrappers", async () => {
    const manager = new ProxyManager({});
    const shellBuiltin = process.platform === "win32" ? "dir" : ":";
    (manager as any).buildLaunchSpecs = () => [
      {
        label: "shell-backed",
        command: shellBuiltin,
        args: [],
        checkCommand: shellBuiltin,
        checkArgs: [],
        useShell: true,
      },
    ];
    const infoSpy = vi.spyOn((manager as any).logger, "info");

    await (manager as any).startLegroomProxy("http://127.0.0.1:8787", 8787);

    expect(infoSpy).toHaveBeenCalledWith(expect.stringContaining("Auto-start launcher selected"));
    expect(infoSpy).toHaveBeenCalledWith(expect.stringContaining("shell-backed"));
  });

  it("throws when no launcher is executable", async () => {
    const manager = new ProxyManager({});
    (manager as any).buildLaunchSpecs = () => [
      {
        label: "none",
        command: "none",
        args: ["proxy"],
        checkCommand: "none",
        checkArgs: ["--version"],
      },
    ];
    (manager as any).canExecute = () => false;

    await expect((manager as any).startLegroomProxy("http://127.0.0.1:8787")).rejects.toThrow(
      /No usable Legroom launcher found/,
    );
  });
});
