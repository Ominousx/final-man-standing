"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setSuccessMessage("");

    try {
      await login(name, email, password);
      setSuccessMessage("Login successful! Redirecting...");
      setTimeout(() => {
        router.push("/");
      }, 1000);
    } catch (err) {
      setError("Invalid credentials. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Image
              src="/icons/vct.png"
              alt="VCT Logo"
              width={64}
              height={64}
              className="object-contain"
            />
          </div>
          <h1 className="text-3xl font-bold text-yellow-400 mb-2">VCT Survivor</h1>
          <p className="text-gray-400">Final Man Standing</p>
        </div>

        <Card className="bg-black border border-gray-800 shadow-2xl">
          <CardHeader className="text-center border-b border-gray-800">
            <CardTitle className="text-2xl text-white">Welcome Back</CardTitle>
            <p className="text-gray-400">Sign in to your account</p>
          </CardHeader>
          <CardContent className="p-6">
            <form onSubmit={handleLogin} className="space-y-6">
              {successMessage && (
                <div className="text-green-400 text-sm text-center bg-green-900/20 border border-green-800 rounded-xl p-3">
                  {successMessage}
                </div>
              )}
              <div className="space-y-2">
                <label htmlFor="name" className="text-sm font-medium text-gray-300">
                  Full Name
                </label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Enter your full name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="bg-gray-900 border-gray-700 text-white placeholder-gray-400 focus:border-white focus:ring-white rounded-xl"
                  required
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium text-gray-300">
                  Email Address
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-gray-900 border-gray-700 text-white placeholder-gray-400 focus:border-white focus:ring-white rounded-xl"
                  required
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium text-gray-300">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-gray-900 border-gray-700 text-white placeholder-gray-400 focus:border-white focus:ring-white rounded-xl"
                  required
                />
              </div>
              {error && (
                <div className="text-red-400 text-sm text-center bg-red-900/20 border border-red-800 rounded-xl p-3">
                  {error}
                </div>
              )}
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full bg-white text-black hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed h-12 text-lg font-semibold rounded-xl transition-all duration-300"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                    <span>Signing In...</span>
                  </div>
                ) : (
                  "Sign In"
                )}
              </Button>
              <div className="text-center">
                <p className="text-gray-400 text-sm mb-2">Demo Credentials:</p>
                <p className="text-gray-500 text-xs">Name: John Doe</p>
                <p className="text-gray-500 text-xs">Email: admin@vct.com</p>
                <p className="text-gray-500 text-xs">Password: password123</p>
              </div>
            </form>
            <div className="mt-6 text-center space-y-3">
              <div className="text-sm">
                <span className="text-gray-400">Don't have an account? </span>
                <Link href="/register" className="text-white hover:text-gray-300 underline">
                  Sign up
                </Link>
              </div>
              <div className="text-sm">
                <Link href="/forgot-password" className="text-gray-400 hover:text-gray-300 underline">
                  Forgot your password?
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-gray-500 text-sm">
            © 2025 VCT Survivor. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}

