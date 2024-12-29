import 'package:kitchenowl/models/household.dart';
import 'package:kitchenowl/models/item.dart';
import 'package:kitchenowl/models/model.dart';

class ShoppingList extends Model {
  final int? id;
  final String name;
  final List<ShoppinglistItem> items;
  final List<ItemWithDescription> recentItems;
  final int? householdId;
  final String? householdName;

  const ShoppingList({
    this.id,
    required this.name,
    this.items = const [],
    this.recentItems = const [],
    this.householdId,
    this.householdName,
  });

  factory ShoppingList.fromJson(Map<String, dynamic> map) {
    List<ShoppinglistItem> items = const [];
    if (map.containsKey('items')) {
      items = List.from(map['items'].map((e) => ShoppinglistItem.fromJson(e)));
    }
    List<ItemWithDescription> recentItems = const [];
    if (map.containsKey('recentItems')) {
      recentItems = List.from(
          map['recentItems'].map((e) => ItemWithDescription.fromJson(e)));
    }

    return ShoppingList(
      id: map['id'],
      name: map['name'],
      items: items,
      recentItems: recentItems,
      householdId: map['household_id'],
      householdName: map['household_name'],
    );
  }

  ShoppingList copyWith({
    String? name,
    List<ShoppinglistItem>? items,
    List<ItemWithDescription>? recentItems,
    int? householdId,
    String? householdName,
  }) =>
      ShoppingList(
        id: id,
        name: name ?? this.name,
        items: items ?? this.items,
        recentItems: recentItems ?? this.recentItems,
        householdId: householdId ?? this.householdId,
        householdName: householdName ?? this.householdName,
      );

  Household? get household => householdId != null ? Household(id: householdId!, name: householdName ?? '') : null;

  @override
  List<Object?> get props => [id, name, items, recentItems, householdId, householdName];

  @override
  Map<String, dynamic> toJson() => {
        "name": name,
      };

  @override
  Map<String, dynamic> toJsonWithId() => toJson()
    ..addAll({
      "id": id,
      "items": items.map((e) => e.toJsonWithId()).toList(),
      "recentItems": recentItems.map((e) => e.toJsonWithId()).toList(),
      if (householdId != null) "household_id": householdId,
      if (householdName != null) "household_name": householdName,
    });
}
