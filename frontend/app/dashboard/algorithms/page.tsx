"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, Code, Play, Trash2 } from "lucide-react";
import { useState } from "react";

interface Algorithm {
  id: string;
  name: string;
  language: string;
  created: string;
  status: string;
}

export default function AlgorithmsPage() {
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([
    {
      id: "1",
      name: "momentum_strategy.py",
      language: "Python",
      created: "2024-01-15",
      status: "Active",
    },
  ]);

  const handleUpload = () => {
    // File upload logic
    alert("Algorithm upload coming soon!");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Algorithms</h1>
          <p className="text-muted-foreground">
            Upload and manage your custom trading strategies
          </p>
        </div>
        <Button onClick={handleUpload}>
          <Upload className="mr-2 h-4 w-4" />
          Upload Algorithm
        </Button>
      </div>

      {/* Algorithms List */}
      <Card>
        <CardHeader>
          <CardTitle>Your Algorithms</CardTitle>
          <CardDescription>Manage your uploaded trading strategies</CardDescription>
        </CardHeader>
        <CardContent>
          {algorithms.length === 0 ? (
            <div className="text-center py-12">
              <Code className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No algorithms yet</h3>
              <p className="text-muted-foreground mb-4">
                Upload your first algorithm to get started
              </p>
              <Button onClick={handleUpload}>
                <Upload className="mr-2 h-4 w-4" />
                Upload Algorithm
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {algorithms.map((algo) => (
                <div
                  key={algo.id}
                  className="p-4 border rounded-lg hover:bg-muted/50 flex items-center justify-between"
                >
                  <div className="flex items-center gap-4">
                    <Code className="h-8 w-8 text-blue-500" />
                    <div>
                      <h3 className="font-semibold">{algo.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {algo.language} • Created {algo.created}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                      {algo.status}
                    </span>
                    <Button variant="outline" size="sm">
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Supported Languages */}
      <Card>
        <CardHeader>
          <CardTitle>Supported Languages</CardTitle>
          <CardDescription>Frameworks and languages you can use</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg">
              <h3 className="font-semibold mb-2">Python</h3>
              <p className="text-sm text-muted-foreground">
                NumPy, Pandas, SciPy, statsmodels
              </p>
            </div>
            <div className="p-4 border rounded-lg">
              <h3 className="font-semibold mb-2">OCaml</h3>
              <p className="text-sm text-muted-foreground">
                Core, Async, Direct market access
              </p>
            </div>
            <div className="p-4 border rounded-lg opacity-60">
              <h3 className="font-semibold mb-2">JavaScript</h3>
              <p className="text-sm text-muted-foreground">
                Coming soon
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
