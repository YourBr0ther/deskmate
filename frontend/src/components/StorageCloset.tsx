/**
 * Storage Closet - Virtual inventory for items not in room
 */

import React, { useEffect, useState } from 'react';

import { useRoomStore } from '../stores/roomStore';
import { StorageItem, Position } from '../types/room';

const StorageCloset: React.FC = () => {
  const {
    storageItems,
    storageVisible,
    toggleStorageVisibility,
    loadStorageItems,
    placeFromStorage,
    moveObjectToStorage,
    objects,
    selectedStorageItemId,
    isStoragePlacementActive,
    startStoragePlacement,
    clearStoragePlacement
  } = useRoomStore();

  // Load storage items when component mounts
  useEffect(() => {
    if (storageVisible) {
      loadStorageItems();
    }
  }, [storageVisible, loadStorageItems]);

  const handleSelectStorageItem = (item: StorageItem) => {
    startStoragePlacement(item.id);
    console.log(`Selected ${item.name} for placement`);
  };

  const handleStoreObject = async (objectId: string) => {
    const obj = objects.find(o => o.id === objectId);
    if (obj && obj.movable) {
      const success = await moveObjectToStorage(objectId);
      if (success) {
        console.log(`Stored ${obj.name} in closet`);
      }
    }
  };

  const getStorageItemColor = (type: string) => {
    switch (type) {
      case 'decoration': return 'bg-purple-600 text-purple-100';
      case 'item': return 'bg-blue-600 text-blue-100';
      case 'tool': return 'bg-green-600 text-green-100';
      default: return 'bg-gray-600 text-gray-100';
    }
  };

  if (!storageVisible) {
    return null;
  }

  return (
    <div className="fixed right-4 top-4 bottom-4 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-40 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <h3 className="text-lg font-semibold text-white">Storage Closet</h3>
        </div>
        <button
          onClick={toggleStorageVisibility}
          className="text-gray-400 hover:text-white transition-colors"
          title="Close Storage Closet"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Storage Items List */}
      <div className="flex-1 overflow-y-auto p-4">
        {isStoragePlacementActive && selectedStorageItemId && (
          <div className="mb-4 p-3 bg-blue-900/50 border border-blue-700 rounded-lg">
            <div className="text-blue-200 text-sm font-medium">Placement Mode</div>
            <div className="text-blue-300 text-xs mt-1">
              Click on the grid to place {storageItems.find(i => i.id === selectedStorageItemId)?.name}
            </div>
            <button
              onClick={clearStoragePlacement}
              className="text-blue-400 hover:text-blue-300 text-xs underline mt-1"
            >
              Cancel
            </button>
          </div>
        )}

        {storageItems.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <div className="text-sm">Storage closet is empty</div>
            <div className="text-xs mt-1">Create items to add them here</div>
          </div>
        ) : (
          <div className="space-y-2">
            {storageItems.map((item) => (
              <div
                key={item.id}
                className={`p-3 rounded-lg border transition-colors cursor-pointer ${
                  selectedStorageItemId === item.id
                    ? 'bg-blue-900/50 border-blue-700'
                    : 'bg-gray-700/50 border-gray-600 hover:bg-gray-600/50'
                }`}
                onClick={() => handleSelectStorageItem(item)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold ${getStorageItemColor(item.type)}`}>
                      {item.name.charAt(0)}
                    </div>
                    <div>
                      <div className="text-white font-medium text-sm">{item.name}</div>
                      <div className="text-gray-400 text-xs">{item.type}</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {item.default_size.width}×{item.default_size.height}
                  </div>
                </div>
                {item.description && (
                  <div className="text-gray-300 text-xs mt-2 line-clamp-2">
                    {item.description}
                  </div>
                )}
                <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                  <span>Used {item.usage_count} times</span>
                  <span>by {item.created_by}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="p-4 border-t border-gray-700">
        <div className="text-sm text-gray-400 mb-2">Quick Actions</div>
        <div className="space-y-2">
          {objects.filter(obj => obj.movable).length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-1">Store movable objects:</div>
              <div className="flex flex-wrap gap-1">
                {objects.filter(obj => obj.movable).map((obj) => (
                  <button
                    key={obj.id}
                    onClick={() => handleStoreObject(obj.id)}
                    className="text-xs px-2 py-1 bg-orange-700 hover:bg-orange-600 text-white rounded transition-colors"
                    title={`Store ${obj.name}`}
                  >
                    {obj.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StorageCloset;