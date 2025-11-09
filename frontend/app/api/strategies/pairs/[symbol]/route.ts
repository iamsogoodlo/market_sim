import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export async function GET(
  request: Request,
  { params }: { params: { symbol: string } }
) {
  try {
    const symbol = params.symbol.toUpperCase();

    // Call Python strategy script
    const { stdout, stderr } = await execAsync(
      `python3 server/quant_engine/pairs_trading.py ${symbol}`,
      { cwd: "/Users/iamsogoodlo/market_sim" }
    );

    if (stderr && !stderr.includes("DeprecationWarning")) {
      console.error(`Strategy error: ${stderr}`);
    }

    const result = JSON.parse(stdout);

    return NextResponse.json(result);
  } catch (error: any) {
    console.error("Error calling pairs strategy:", error);
    return NextResponse.json(
      {
        rating: 3,
        metrics: {},
        rationale: `Error: ${error.message}`,
      },
      { status: 500 }
    );
  }
}
