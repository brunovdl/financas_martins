'use client'

import React, { useState } from 'react'
import { X, Plus, Pencil, Trash2, Check, Tag, AlertCircle } from 'lucide-react'
import type { CategoryTheme, ThemeTokens } from '@/lib/theme'

export const COLOR_PALETTE = [
  '#94A3B8', // Slate
  '#5EA8F2', // Blue
  '#B399F5', // Purple
  '#F5738C', // Pink
  '#F2B84B', // Amber
  '#3FD6C4', // Teal
  '#10B981', // Emerald
  '#F97316', // Orange
  '#EC4899', // Rose
  '#8B5CF6', // Violet
]

interface CategoriesModalProps {
  T: ThemeTokens
  categories: CategoryTheme[]
  onClose: () => void
  onAddCategory: (name: string, color: string) => Promise<void>
  onUpdateCategory: (id: string, name: string, color: string) => Promise<void>
  onDeleteCategory: (id: string) => Promise<void>
}

export function CategoriesModal({
  T,
  categories,
  onClose,
  onAddCategory,
  onUpdateCategory,
  onDeleteCategory,
}: CategoriesModalProps) {
  // New category form state
  const [newName, setNewName] = useState('')
  const [newColor, setNewColor] = useState(COLOR_PALETTE[1])
  const [isAdding, setIsAdding] = useState(false)

  // Editing state
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editColor, setEditColor] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  // Deleting confirmation state
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  // Error handling
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    setErrorMsg(null)
    setIsAdding(true)
    try {
      await onAddCategory(newName.trim(), newColor)
      setNewName('')
      setNewColor(COLOR_PALETTE[Math.floor(Math.random() * COLOR_PALETTE.length)])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro ao criar categoria'
      setErrorMsg(msg.includes('duplicate') ? 'Já existe uma categoria com este nome.' : msg)
    } finally {
      setIsAdding(false)
    }
  }

  const startEdit = (cat: CategoryTheme) => {
    setEditingId(cat.id)
    setEditName(cat.name)
    setEditColor(cat.dark || cat.light || COLOR_PALETTE[0])
    setDeletingId(null)
    setErrorMsg(null)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditName('')
    setEditColor('')
  }

  const handleSaveEdit = async (id: string) => {
    if (!editName.trim()) return
    setErrorMsg(null)
    setIsSaving(true)
    try {
      await onUpdateCategory(id, editName.trim(), editColor)
      setEditingId(null)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro ao atualizar categoria'
      setErrorMsg(msg.includes('duplicate') ? 'Já existe uma categoria com este nome.' : msg)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    setErrorMsg(null)
    setIsDeleting(true)
    try {
      await onDeleteCategory(id)
      setDeletingId(null)
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Erro ao excluir categoria')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div
        className="w-full max-w-lg rounded-2xl border shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
        style={{
          backgroundColor: T.surfaceSolid,
          borderColor: T.border,
          color: T.textPrimary,
        }}
      >
        {/* Modal Header */}
        <div
          className="flex items-center justify-between px-6 py-4 border-b shrink-0"
          style={{ borderColor: T.border }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="p-2 rounded-xl"
              style={{ backgroundColor: `${T.accent}15`, color: T.accent }}
            >
              <Tag size={18} />
            </div>
            <div>
              <h2 className="font-display text-lg font-semibold leading-tight">
                Gerenciar Categorias
              </h2>
              <p className="text-xs" style={{ color: T.textFaint }}>
                Crie, edite ou remova categorias do sistema
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full transition-colors hover:opacity-80"
            style={{ color: T.textMuted }}
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        {/* Error Notification */}
        {errorMsg && (
          <div
            className="mx-6 mt-4 p-3 rounded-xl border flex items-center gap-2 text-xs"
            style={{
              backgroundColor: `${T.danger}15`,
              borderColor: `${T.danger}40`,
              color: T.danger,
            }}
          >
            <AlertCircle size={15} className="shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* Form: Incluir Nova Categoria */}
          <form
            onSubmit={handleAdd}
            className="p-4 rounded-xl border space-y-3"
            style={{ backgroundColor: T.surface, borderColor: T.borderSubtle }}
          >
            <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: T.textFaint }}>
              Nova Categoria
            </div>
            <div className="flex flex-col sm:flex-row gap-2.5">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Nome da categoria (ex: Educação)"
                className="flex-1 px-3 py-2 rounded-xl text-sm border outline-none transition-colors"
                style={{
                  backgroundColor: T.inputBg,
                  borderColor: T.border,
                  color: T.textPrimary,
                }}
              />
              <button
                type="submit"
                disabled={isAdding || !newName.trim()}
                className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 shrink-0"
                style={{
                  background: `linear-gradient(90deg, ${T.accent}, ${T.accentTo})`,
                  color: T.accentOnBrand,
                }}
              >
                <Plus size={16} strokeWidth={2.5} />
                {isAdding ? 'Criando...' : 'Adicionar'}
              </button>
            </div>

            {/* Selector de cor */}
            <div>
              <div className="text-[11px] mb-1.5" style={{ color: T.textMuted }}>
                Selecione a cor:
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {COLOR_PALETTE.map((hex) => (
                  <button
                    key={hex}
                    type="button"
                    onClick={() => setNewColor(hex)}
                    className={`w-6 h-6 rounded-full transition-all border ${
                      newColor === hex ? 'scale-110 ring-2 ring-offset-1 ring-emerald-400' : 'opacity-80 hover:opacity-100'
                    }`}
                    style={{ backgroundColor: hex, borderColor: 'transparent' }}
                  />
                ))}
                <input
                  type="color"
                  value={newColor}
                  onChange={(e) => setNewColor(e.target.value)}
                  className="w-7 h-7 rounded-lg cursor-pointer border-0 p-0 bg-transparent"
                  title="Cor personalizada"
                />
              </div>
            </div>
          </form>

          {/* List of Categories */}
          <div className="space-y-2">
            <div className="text-xs font-semibold uppercase tracking-wider px-1" style={{ color: T.textFaint }}>
              Categorias Existentes ({categories.length})
            </div>

            <div className="space-y-1.5">
              {categories.map((cat) => {
                const color = cat.dark || cat.light || COLOR_PALETTE[0]
                const isEditing = editingId === cat.id
                const isConfirmingDelete = deletingId === cat.id

                if (isEditing) {
                  return (
                    <div
                      key={cat.id}
                      className="p-3 rounded-xl border space-y-3"
                      style={{ backgroundColor: T.surface, borderColor: T.accent }}
                    >
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="flex-1 px-3 py-1.5 rounded-lg text-sm border outline-none"
                          style={{
                            backgroundColor: T.inputBg,
                            borderColor: T.border,
                            color: T.textPrimary,
                          }}
                          autoFocus
                        />
                        <button
                          onClick={() => handleSaveEdit(cat.id)}
                          disabled={isSaving || !editName.trim()}
                          className="p-2 rounded-lg text-white font-medium text-xs flex items-center justify-center transition-opacity disabled:opacity-50"
                          style={{ backgroundColor: T.accent }}
                          title="Salvar"
                        >
                          <Check size={16} />
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="p-2 rounded-lg border text-xs flex items-center justify-center hover:opacity-80"
                          style={{ borderColor: T.border, color: T.textMuted }}
                          title="Cancelar"
                        >
                          <X size={16} />
                        </button>
                      </div>

                      {/* Selector de cor no edit */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        {COLOR_PALETTE.map((hex) => (
                          <button
                            key={hex}
                            type="button"
                            onClick={() => setEditColor(hex)}
                            className={`w-5 h-5 rounded-full border transition-all ${
                              editColor === hex ? 'scale-110 ring-2 ring-emerald-400' : 'opacity-70 hover:opacity-100'
                            }`}
                            style={{ backgroundColor: hex, borderColor: 'transparent' }}
                          />
                        ))}
                        <input
                          type="color"
                          value={editColor}
                          onChange={(e) => setEditColor(e.target.value)}
                          className="w-6 h-6 rounded border-0 p-0 cursor-pointer bg-transparent"
                        />
                      </div>
                    </div>
                  )
                }

                if (isConfirmingDelete) {
                  return (
                    <div
                      key={cat.id}
                      className="p-3 rounded-xl border flex items-center justify-between gap-3 text-xs"
                      style={{
                        backgroundColor: `${T.danger}10`,
                        borderColor: `${T.danger}40`,
                      }}
                    >
                      <span style={{ color: T.textPrimary }}>
                        Excluir <strong>{cat.name}</strong>?
                      </span>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => handleDelete(cat.id)}
                          disabled={isDeleting}
                          className="px-3 py-1 rounded-lg text-white font-semibold text-xs transition-opacity disabled:opacity-50"
                          style={{ backgroundColor: T.danger }}
                        >
                          {isDeleting ? 'Excluindo...' : 'Sim, excluir'}
                        </button>
                        <button
                          onClick={() => setDeletingId(null)}
                          className="px-3 py-1 rounded-lg border text-xs hover:opacity-80"
                          style={{ borderColor: T.border, color: T.textMuted }}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )
                }

                return (
                  <div
                    key={cat.id}
                    className="flex items-center justify-between p-3 rounded-xl border transition-colors group"
                    style={{
                      backgroundColor: T.surface,
                      borderColor: T.borderSubtle,
                    }}
                  >
                    <div className="flex items-center gap-2.5">
                      <span
                        className="w-3.5 h-3.5 rounded-full shrink-0 shadow-sm"
                        style={{ backgroundColor: color }}
                      />
                      <span className="font-medium text-sm" style={{ color: T.textPrimary }}>
                        {cat.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 opacity-90 group-hover:opacity-100">
                      <button
                        onClick={() => startEdit(cat)}
                        className="p-1.5 rounded-lg border transition-colors hover:opacity-80"
                        style={{ borderColor: T.borderSubtle, color: T.textMuted }}
                        title="Editar categoria"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        onClick={() => setDeletingId(cat.id)}
                        className="p-1.5 rounded-lg border transition-colors hover:opacity-80"
                        style={{
                          borderColor: `${T.danger}30`,
                          color: T.danger,
                          backgroundColor: `${T.danger}0A`,
                        }}
                        title="Excluir categoria"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                )
              })}

              {categories.length === 0 && (
                <div className="text-center py-6 text-xs" style={{ color: T.textFaint }}>
                  Nenhuma categoria cadastrada.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div
          className="px-6 py-3 border-t flex justify-end shrink-0"
          style={{ borderColor: T.border, backgroundColor: T.surface }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-sm font-medium border transition-colors hover:opacity-80"
            style={{ borderColor: T.border, color: T.textPrimary }}
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  )
}
