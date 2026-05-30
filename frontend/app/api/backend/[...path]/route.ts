import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const INTERNAL_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

const API_BASIC_AUTH_USERNAME = process.env.API_BASIC_AUTH_USERNAME;
const API_BASIC_AUTH_PASSWORD = process.env.API_BASIC_AUTH_PASSWORD;

const ENABLE_BACKEND_PROXY_IN_PRODUCTION =
  process.env.ENABLE_BACKEND_PROXY_IN_PRODUCTION === "true";

const ALLOWED_BACKEND_PATH_PREFIXES = (
  process.env.BACKEND_PROXY_ALLOWED_PREFIXES ??
  [
    "/ui-api",
    "/seniors",
    "/calls",
    "/operator-actions",
    "/check-ins",
    "/schedules",
    "/scheduler",
    "/operational-status",
    "/ai-call-sessions",
    "/support-contacts",
    "/heat-settings",
  ].join(",")
)
  .split(",")
  .map((prefix) => prefix.trim())
  .filter(Boolean);

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

function jsonError(message: string, status: number): NextResponse {
  return NextResponse.json(
    {
      error: message,
    },
    {
      status,
    }
  );
}

function encodeBasicAuth(username: string, password: string): string {
  return Buffer.from(`${username}:${password}`, "utf-8").toString("base64");
}

function pathMatchesPrefix(path: string, prefix: string): boolean {
  return path === prefix || path.startsWith(`${prefix}/`);
}

function isAllowedBackendPath(path: string): boolean {
  return ALLOWED_BACKEND_PATH_PREFIXES.some((prefix) =>
    pathMatchesPrefix(path, prefix)
  );
}

function assertProxyAllowedForEnvironment(): NextResponse | null {
  if (
    process.env.NODE_ENV === "production" &&
    !ENABLE_BACKEND_PROXY_IN_PRODUCTION
  ) {
    return jsonError(
      "Backend proxy is disabled in production. Set ENABLE_BACKEND_PROXY_IN_PRODUCTION=true only after real frontend user authentication is enforced.",
      403
    );
  }

  return null;
}

function assertBackendCredentialsAvailable(): NextResponse | null {
  if (
    process.env.NODE_ENV === "production" &&
    ENABLE_BACKEND_PROXY_IN_PRODUCTION &&
    (!API_BASIC_AUTH_USERNAME || !API_BASIC_AUTH_PASSWORD)
  ) {
    return jsonError(
      "Backend proxy is enabled in production, but backend credentials are not configured.",
      500
    );
  }

  return null;
}

function buildBackendPath(pathParts: string[] | undefined): string {
  return `/${(pathParts ?? []).join("/")}`;
}

function buildBackendUrl(backendPath: string, request: NextRequest): string {
  const backendUrl = new URL(backendPath, INTERNAL_API_BASE_URL);

  request.nextUrl.searchParams.forEach((value, key) => {
    backendUrl.searchParams.append(key, value);
  });

  return backendUrl.toString();
}

function buildForwardHeaders(request: NextRequest): Headers {
  const headers = new Headers();

  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  const accept = request.headers.get("accept");
  if (accept) {
    headers.set("accept", accept);
  }

  if (API_BASIC_AUTH_USERNAME && API_BASIC_AUTH_PASSWORD) {
    headers.set(
      "authorization",
      `Basic ${encodeBasicAuth(API_BASIC_AUTH_USERNAME, API_BASIC_AUTH_PASSWORD)}`
    );
  }

  return headers;
}

function buildResponseHeaders(backendResponse: Response): Headers {
  const headers = new Headers();

  backendResponse.headers.forEach((value, key) => {
    const normalizedKey = key.toLowerCase();

    if (HOP_BY_HOP_HEADERS.has(normalizedKey)) {
      return;
    }

    if (normalizedKey === "content-encoding") {
      return;
    }

    if (normalizedKey === "content-length") {
      return;
    }

    headers.set(key, value);
  });

  return headers;
}

async function proxyRequest(
  request: NextRequest,
  context: { params: Promise<{ path?: string[] }> }
): Promise<Response> {
  const environmentError = assertProxyAllowedForEnvironment();
  if (environmentError) {
    return environmentError;
  }

  const credentialsError = assertBackendCredentialsAvailable();
  if (credentialsError) {
    return credentialsError;
  }

  const { path } = await context.params;
  const backendPath = buildBackendPath(path);

  if (!isAllowedBackendPath(backendPath)) {
    return jsonError(
      `Backend proxy path is not allowed: ${backendPath}`,
      403
    );
  }

  const backendUrl = buildBackendUrl(backendPath, request);
  const method = request.method.toUpperCase();
  const hasBody = !["GET", "HEAD"].includes(method);

  const backendResponse = await fetch(backendUrl, {
    method,
    headers: buildForwardHeaders(request),
    body: hasBody ? await request.arrayBuffer() : undefined,
    cache: "no-store",
  });

  const responseHeaders = buildResponseHeaders(backendResponse);

  if (backendResponse.status === 204) {
    return new Response(null, {
      status: 204,
      headers: responseHeaders,
    });
  }

  return new Response(await backendResponse.arrayBuffer(), {
    status: backendResponse.status,
    statusText: backendResponse.statusText,
    headers: responseHeaders,
  });
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, context);
}