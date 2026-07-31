import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'
import path from 'node:path'
import fs from 'node:fs'

const globalForMcp = globalThis as unknown as {
  cataCentavoClient?: Promise<Client>
}

function resolvePluggyItemIds(): string {
  if (process.env.PLUGGY_ITEM_IDS && process.env.PLUGGY_ITEM_IDS.trim().length > 0) {
    return process.env.PLUGGY_ITEM_IDS.trim()
  }

  // Fallback: auto-concatenate all PLUGGY_ITEM_ID_* env variables
  const itemIds = Object.keys(process.env)
    .filter((key) => key.startsWith('PLUGGY_ITEM_ID'))
    .map((key) => process.env[key]?.trim())
    .filter((val): val is string => !!val && val.length > 0)

  if (itemIds.length > 0) {
    return itemIds.join(',')
  }

  throw new Error('Nenhuma chave de item da Pluggy (PLUGGY_ITEM_IDS ou PLUGGY_ITEM_ID_*) encontrada no ambiente.')
}

function requiredEnv(name: string): string {
  const v = process.env[name]
  if (!v) {
    if (name === 'PLUGGY_ITEM_IDS') {
      return resolvePluggyItemIds()
    }
    throw new Error(`Variável de ambiente ${name} não configurada.`)
  }
  return v
}

function resolveDataDirectories(): { cacheDir: string; dataDir: string; stateDir: string } {
  let cacheDir = process.env.XDG_CACHE_HOME || '/data/cata-centavo/cache'
  let dataDir = process.env.XDG_DATA_HOME || '/data/cata-centavo/data'
  let stateDir = process.env.XDG_STATE_HOME || '/data/cata-centavo/state'

  try {
    fs.mkdirSync(cacheDir, { recursive: true })
    fs.mkdirSync(dataDir, { recursive: true })
    fs.mkdirSync(stateDir, { recursive: true })
  } catch (e) {
    // Fallback if system path (like /data) is not writable
    const fallbackBase = path.join(process.cwd(), '.tmp', 'cata-centavo')
    cacheDir = path.join(fallbackBase, 'cache')
    dataDir = path.join(fallbackBase, 'data')
    stateDir = path.join(fallbackBase, 'state')
    fs.mkdirSync(cacheDir, { recursive: true })
    fs.mkdirSync(dataDir, { recursive: true })
    fs.mkdirSync(stateDir, { recursive: true })
  }

  return { cacheDir, dataDir, stateDir }
}

async function connect(): Promise<Client> {
  const clientId = requiredEnv('PLUGGY_CLIENT_ID')
  const clientSecret = requiredEnv('PLUGGY_CLIENT_SECRET')
  const itemIds = resolvePluggyItemIds()
  const { cacheDir, dataDir, stateDir } = resolveDataDirectories()

  const binPath = path.join(process.cwd(), 'node_modules/cata-centavo/dist/bin/cata-centavo.js')

  const transport = new StdioClientTransport({
    command: 'node',
    args: ['--no-warnings', binPath],
    env: {
      ...process.env,
      NODE_NO_WARNINGS: '1',
      NODE_OPTIONS: '--no-warnings',
      PLUGGY_CLIENT_ID: clientId,
      PLUGGY_CLIENT_SECRET: clientSecret,
      PLUGGY_ITEM_IDS: itemIds,
      XDG_CACHE_HOME: cacheDir,
      XDG_DATA_HOME: dataDir,
      XDG_STATE_HOME: stateDir,
    },
  })

  const client = new Client({ name: 'mai-finance', version: '1.0.0' }, { capabilities: {} })

  client.onclose = () => {
    console.warn('[cata-centavo] Conexão MCP encerrada. Limpando cache do client.')
    globalForMcp.cataCentavoClient = undefined
  }

  await client.connect(transport)
  return client
}

export function getCataCentavoClient(): Promise<Client> {
  if (!globalForMcp.cataCentavoClient) {
    globalForMcp.cataCentavoClient = connect().catch((err) => {
      globalForMcp.cataCentavoClient = undefined
      throw err
    })
  }
  return globalForMcp.cataCentavoClient
}

export function resetCataCentavoClient(): void {
  globalForMcp.cataCentavoClient = undefined
}
