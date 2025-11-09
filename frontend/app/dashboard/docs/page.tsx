import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, ExternalLink } from "lucide-react";
import Link from "next/link";

export default function DocsPage() {
  const docs = [
    {
      title: "Platform Vision",
      description: "Complete overview of MarketSim's quantitative trading platform",
      link: "https://github.com/iamsogoodlo/market_sim/blob/main/README_VISION.md",
    },
    {
      title: "Getting Started",
      description: "Installation and setup guide",
      link: "https://github.com/iamsogoodlo/market_sim#quick-start",
    },
    {
      title: "Quantitative Strategies",
      description: "Technical specifications for 7 strategies",
      link: "https://github.com/iamsogoodlo/market_sim/blob/main/README_VISION.md#-quantitative-strategies---technical-specification",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Documentation</h1>
        <p className="text-muted-foreground">
          Learn how to use MarketSim
        </p>
      </div>

      <div className="grid gap-4">
        {docs.map((doc, idx) => (
          <Card key={idx}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                {doc.title}
              </CardTitle>
              <CardDescription>{doc.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Link
                href={doc.link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline flex items-center gap-2"
              >
                View Documentation
                <ExternalLink className="h-4 w-4" />
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
