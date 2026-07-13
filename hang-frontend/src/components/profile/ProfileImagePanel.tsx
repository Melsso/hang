import { useState, useEffect } from "react";
import { DndContext, closestCenter } from "@dnd-kit/core";
import type { DragEndEvent } from "@dnd-kit/core";
import { arrayMove, SortableContext, verticalListSortingStrategy, useSortable } from "@dnd-kit/sortable";

import { CSS } from "@dnd-kit/utilities";
import defaultUserImage from "../../assets/default_user.png"

export type ProfileImage = {
    image_id: number;
    image_url: string;
};

const DEFAULT_IMAGE_URL = defaultUserImage;

type Props = {
    images: ProfileImage[];
    imageOrder: ProfileImage[];
    setImageOrder: React.Dispatch<React.SetStateAction<ProfileImage[]>>;
    deletedImages: number[];
    setDeletedImages: React.Dispatch<React.SetStateAction<number[]>>;
    editMode: boolean;
    canEdit: boolean;
    onUploadImages?: (e: React.ChangeEvent<HTMLInputElement>) => void;
};

function SortItem({
    image,
    deleted,
    onToggleDelete,
}: {
    image: ProfileImage;
    deleted: boolean;
    onToggleDelete: (id: number) => void;
}) {
    const {
        setNodeRef,
        listeners,
        attributes,
        transform,
        transition,
    } = useSortable({
        id: image.image_id,
    });

    return (
        <div
            ref={setNodeRef}
            style={{
                transform: CSS.Transform.toString(transform),
                transition,
            }}
            className={`
                flex items-center gap-3 p-3 rounded-lg
                transition-all
                ${deleted
                    ? "bg-red-900/60 border border-red-500"
                    : "bg-[#222] border border-transparent"}
            `}
        >
            <img
                src={image.image_url}
                className="w-12 h-12 object-cover rounded"
            />

            <span className="text-white text-sm flex-1">
                Image
            </span>

            <button
                type="button"
                onClick={() => onToggleDelete(image.image_id)}
                className={`
                    px-3 py-1 rounded text-xs
                    ${deleted
                        ? "bg-red-600 text-white"
                        : "bg-[#333] text-white/70"}
                `}
            >
                {deleted ? "Marked" : "Delete"}
            </button>

            <div
                {...attributes}
                {...listeners}
                className="cursor-grab text-white/50 px-2"
            >
                ☰
            </div>
        </div>
    );
}

export default function ProfileImagePanel({ images, imageOrder, setImageOrder, deletedImages, setDeletedImages, editMode, canEdit, onUploadImages }: Props) {
    const [selectedIndex, setSelectedIndex] = useState(0);
    const activeImages = editMode ? imageOrder : images;
    const hasImages = activeImages.length > 0;
    const featured = hasImages ? activeImages[selectedIndex] : null;
    const prev = () => setSelectedIndex((p) => p === 0 ? activeImages.length - 1 : p - 1);
    const next = () => setSelectedIndex((p) => p === activeImages.length - 1 ? 0 : p + 1);

    useEffect(() => {
        setSelectedIndex(0);
    }, [images]);

    const toggleDelete = (imageId: number) => {setDeletedImages((prev) => prev.includes(imageId) ? prev.filter((id) => id !== imageId) : [...prev, imageId]);};

    const handleDragEnd = (e: DragEndEvent) => {
        const { active, over } = e;
        if (!over || active.id === over.id) return;
        const oldIndex = imageOrder.findIndex((i) => i.image_id === active.id);
        const newIndex = imageOrder.findIndex((i) => i.image_id === over.id);
        setImageOrder(arrayMove(imageOrder, oldIndex, newIndex));
    };

    return (
        <div className="w-1/2 flex flex-col bg-[#181818] border-r">

            {!editMode && (
                <div className="w-full h-8/10 relative bg-black">
                    <img
                        src={hasImages ? featured!.image_url : DEFAULT_IMAGE_URL}
                        className="h-full w-full p-2 object-cover"
                    />

                    {hasImages && activeImages.length > 1 && (
                        <>
                            <button
                                onClick={prev}
                                className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-black/60 text-white rounded-full"
                            >
                                ←
                            </button>

                            <button
                                onClick={next}
                                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-black/60 text-white rounded-full"
                            >
                                →
                            </button>
                        </>
                    )}
                </div>
            )}

            {editMode && (
                <div className="flex flex-col gap-3 p-4 overflow-y-auto">

                    {imageOrder.length === 0 ? (
                        <p className="text-sm text-white/40 text-center py-6">
                            No images yet
                        </p>
                    ) : (
                        <DndContext
                            collisionDetection={closestCenter}
                            onDragEnd={handleDragEnd}
                        >
                            <SortableContext
                                items={imageOrder.map((i) => i.image_id)}
                                strategy={verticalListSortingStrategy}
                            >
                                {imageOrder.map((img) => (
                                    <SortItem
                                        key={img.image_id}
                                        image={img}
                                        deleted={deletedImages.includes(img.image_id)}
                                        onToggleDelete={toggleDelete}
                                    />
                                ))}
                            </SortableContext>
                        </DndContext>
                    )}

                    {imageOrder.length > 0 && (
                        <p className="text-xs text-white/40">
                            Drag to reorder images
                        </p>
                    )}
                </div>
            )}

            {canEdit && !editMode && (
                <div className="p-4">
                    <label className="cursor-pointer">
                        <div className="py-3 text-center bg-[#e50914] text-white rounded-xl">
                            Upload Pictures
                        </div>

                        <input
                            type="file"
                            multiple
                            className="hidden"
                            onChange={onUploadImages}
                        />
                    </label>
                </div>
            )}
        </div>
    );
}