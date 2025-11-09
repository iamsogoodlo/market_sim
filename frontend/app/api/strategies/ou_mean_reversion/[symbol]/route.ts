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
    const { stdout } = await execAsync(
      `python3 server/quant_engine/ou_mean_reversion.py ${symbol}`,
      { cwd: "/Users/iamsogoodlo/market_sim" }
    );
    return NextResponse.json(JSON.parse(stdout));
  } catch (error: any) {
    return NextResponse.json(
      { rating: 3, metrics: {}, rationale: `Error: ${error.message}` },
      { status: 500 }
    );
  }
}
