import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// Protect all routes by default. If you want to make specific routes public,
// you can define them here or adjust the matcher.
const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)', 
  '/sign-up(.*)',
  '/api/(.*)' // Keep backend APIs public if they don't use Clerk verification yet
]);

export default clerkMiddleware(async (auth, req) => {
  const { userId } = await auth();

  if (!isPublicRoute(req)) {
    if (!userId) {
      await auth.protect();
    }
  }

  // Append user ID to headers so the backend can read it securely
  const requestHeaders = new Headers(req.headers);
  if (userId) {
    requestHeaders.set("x-user-id", userId);
  }
  // Add a shared secret to ensure the backend only trusts requests from this frontend
  requestHeaders.set("x-api-key", process.env.BACKEND_API_SECRET || "websual_dev_secret_key");

  return NextResponse.next({
    request: {
      headers: requestHeaders,
    }
  });
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};
