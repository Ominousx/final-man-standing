"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      if (password !== confirmPassword) {
        setError("Passwords do not match");
        return;
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (name && email && password && password.length >= 6) {
        router.push("/login?message=Registration successful! Please log in.");
      } else {
        setError("Please enter a valid name, email and password (minimum 6 characters)");
      }
    } catch (err) {
      setError("Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 mb-4">
            <Image
              src="/icons/vct.png"
              alt="VCT Logo"
              width={64}
              height={64}
              className="object-contain"
            />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">VCT Survivor</h1>
          <p className="text-gray-400">Tournament Pool Management</p>
        </div>

        <Card className="bg-black border border-gray-800 shadow-2xl">
          <CardHeader className="text-center border-b border-gray-800">
            <CardTitle className="text-2xl text-white">Create Account</CardTitle>
            <p className="text-gray-400">Join the tournament management platform</p>
          </CardHeader>
          <CardContent className="p-6">
            <form onSubmit={handleRegister} className="space-y-6">
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
                  placeholder="Create a password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-gray-900 border-gray-700 text-white placeholder-gray-400 focus:border-white focus:ring-white rounded-xl"
                  required
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-300">
                  Confirm Password
                </label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
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
                    <span>Creating Account...</span>
                  </div>
                ) : (
                  "Create Account"
                )}
              </Button>
            </form>
            <div className="mt-6 text-center">
              <div className="text-sm">
                <span className="text-gray-400">Already have an account? </span>
                <Link href="/login" className="text-white hover:text-gray-300 underline">
                  Sign in
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
        <div className="text-center mt-8">
          <p className="text-gray-500 text-sm">
            © 2025 VCT Survivor. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
