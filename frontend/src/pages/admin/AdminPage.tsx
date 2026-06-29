/**
 * Interface d'administration (Lot 8) — réservée aux comptes staff.
 *
 * Une page à onglets : Vue d'ensemble · Config LLM · Config app · Utilisateurs ·
 * Données. Chaque onglet est un composant dédié (dossier pages/admin/).
 */
import { useState } from 'react';
import OverviewTab from './OverviewTab';
import LLMConfigTab from './LLMConfigTab';
import SiteConfigTab from './SiteConfigTab';
import UsersTab from './UsersTab';
import DataTab from './DataTab';

type TabKey = 'overview' | 'llm' | 'site' | 'users' | 'data';

const TABS: { key: TabKey; label: string }[] = [
  { key: 'overview', label: "Vue d'ensemble" },
  { key: 'llm', label: 'Config LLM' },
  { key: 'site', label: 'Config app' },
  { key: 'users', label: 'Utilisateurs' },
  { key: 'data', label: 'Données' },
];

export default function AdminPage() {
  const [tab, setTab] = useState<TabKey>('overview');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Administration</h1>
        <p className="text-slate-500 text-sm">
          Réservé aux administrateurs. Configurez l'application, le LLM et gérez les utilisateurs.
        </p>
      </div>

      {/* Onglets */}
      <div className="border-b border-slate-200 flex flex-wrap gap-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              tab === t.key
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && <OverviewTab />}
      {tab === 'llm' && <LLMConfigTab />}
      {tab === 'site' && <SiteConfigTab />}
      {tab === 'users' && <UsersTab />}
      {tab === 'data' && <DataTab />}
    </div>
  );
}
